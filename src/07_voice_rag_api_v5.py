import os
import uvicorn
import io
import logging
# import time         # 속도 측정외 사용하지 않음.
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from faster_whisper import WhisperModel

# v5 설정 및 교정 함수 로드
from config import Settings
from alias_map import clean_and_refine

logger = logging.getLogger("uvicorn")

# 1. v5 초기화 및 설정 (기존 값 주석 보존)
# DB_PATH = "./chroma_db"
db_path = str(Settings.CHROMA_DB_PATH)
# COLLECTION_NAME = "project_docs"
collection_name = Settings.CHROMA_COLLECTION_NAME

app = FastAPI(title="FS Voice RAG System v5")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG 컴포넌트 로드 (v5 임베딩 동기화)
# embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
embeddings = OpenAIEmbeddings(model=Settings.EMBEDDING_MODEL)

vector_db = Chroma(
    persist_directory=db_path,
    embedding_function=embeddings,
    collection_name=collection_name
)
# llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
llm = ChatOpenAI(model_name=Settings.OPENAI_MODEL, temperature=0)

# Whisper 모델 로드 (기존 유지)
stt_model = WhisperModel("large-v3", device="cpu", compute_type="int8")

# 2. 공통 검색 로직 (v5 표준: 본문 정제 및 메타데이터 추출)
def perform_rag_search(query: str):
    refined_query = clean_and_refine(query)
    
    # 검색 K값 Settings 연동
    # docs = vector_db.similarity_search(refined_query, k=5)
    docs = vector_db.similarity_search(refined_query, k=Settings.VECTOR_SEARCH_K)
    
    context_list = []
    sources = []
    
    for d in docs:
        context_list.append(d.page_content)
        raw_src = d.metadata.get(Settings.META_SOURCE_KEY, "알 수 없음")
              
        fname = os.path.basename(raw_src)
        if "_" in fname and fname.endswith(".txt"):       # [수정] .txt 및 해시값 제거하여 원본 파일명 복원 # 뒤에서부터 첫 번째 '_'를 찾아 그 앞부분만 남김 (해시 제거)
            clean_name = fname.rsplit('_', 1)[0]
            sources.append(clean_name)
        else:
            sources.append(fname.replace(".txt", ""))

   
    sources = sorted(list(set(sources)))
    context = "\n\n".join(context_list)
    
    # v5 프롬프트 (간결성 유지)
    # prompt = f"다음 문맥을 바탕으로 질문에 정확히 답하세요:\n\n{context}\n\n질문: {refined_query}"
    # 정보가 없는 질문에 대해 지나치게 오래 생각하는 것을 방지
    # 수정 후 (엄격함과 속도 동시 확보)# 수정 후 (시간 압박 제거 및 지식 추출 강조)
    prompt = (
        f"너는 신속하고 정확한 지식 비서야. [문맥]을 바탕으로 질문에 답해.\n"
        f"1. [문맥]에 답변과 관련된 내용이 조금이라도 있다면 그 근거를 사용해 답변해.\n"
        f"2. 만약 [문맥]에서 도저히 답을 찾을 수 없는 경우에만 '현재 문서에서는 해당 내용을 찾을 수 없습니다'라고 답해.\n"
        f"3. 억지로 지어내지는 말되, 문맥 내의 정보를 최대한 활용해줘.\n\n"
        f"[문맥]: {context}\n\n"
        f"[질문]: {refined_query}"
    )


    
    try:
        response = llm.invoke(prompt)
        answer = response.content
    except Exception as e:
        logger.error(f"LLM 에러: {e}")
        answer = "답변 생성 중 오류가 발생했습니다."

    return {
        "original_text": query,
        "refined_query": refined_query,
        "answer": answer,
        "sources": sources
    }

# 3. API 엔드포인트 (config v5 규격 반영)
class ChatRequest(BaseModel):
    message: str = None
    text: str = None

@app.post(Settings.ENDPOINT_CHAT)
@app.post(Settings.ENDPOINT_QUERY)
async def chat_text(request: ChatRequest):
    query_text = request.message or request.text
    if not query_text:
        raise HTTPException(status_code=400, detail="질문이 없습니다.")
    return perform_rag_search(query_text)

@app.post(Settings.ENDPOINT_VOICE)
async def chat_voice(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        segments, _ = stt_model.transcribe(io.BytesIO(audio_bytes), beam_size=5, language="ko")
        voice_text = " ".join([s.text for s in segments])
        return perform_rag_search(voice_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 포트 번호 Settings 연동
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    uvicorn.run(app, host="0.0.0.0", port=Settings.API_PORT)
