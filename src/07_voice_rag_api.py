import os
import uvicorn
import io
import logging # 추가
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# 원본: from langchain_openai import OpenAIEmbeddings, ChatOpenAI
# 수정본: 로컬 임베딩 사용을 위한 라이브러리 추가
from langchain_community.embeddings import HuggingFaceEmbeddings 
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from faster_whisper import WhisperModel

# 설정 파일 로드 (추가)
from config import Settings
from alias_map import clean_and_refine

# 로거 설정
logger = logging.getLogger("uvicorn")

# 1. 초기화 및 설정
# 원본: DB_PATH = "./chroma_db"
# 원본: COLLECTION_NAME = "project_docs"
# 수정본: config.py의 설정을 강제 연결 (불일치 시 에러 발생)
DB_PATH = str(Settings.CHROMA_DB_PATH)
COLLECTION_NAME = Settings.CHROMA_COLLECTION_NAME
EMBEDDING_MODEL_NAME = Settings.EMBEDDING_MODEL

app = FastAPI(title="FS Voice RAG System (large-v3)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG 컴포넌트 로드
# 원본: embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
# 수정본: 2.3GB DB를 만든 로컬 모델과 동일하게 설정 (핵심!)
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL_NAME,
    model_kwargs={'device': 'cpu'}
)

vector_db = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME
)
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

# Whisper Large-v3 모델 로드 (i7-14700 / 32GB RAM 최적화)
print("⏳ Whisper STT 엔진(Large-v3) 로딩 중... (약 3GB)")
stt_model = WhisperModel("large-v3", device="cpu", compute_type="int8")

print("✅ 엔진 준비 완료")

# 2. 공통 검색 로직
def perform_rag_search(query: str):
    refined_query = clean_and_refine(query)
    print(f"🔍 [최종 교정 쿼리]: {refined_query}")
    
    # 원본: docs = vector_db.similarity_search(refined_query, k=5)
    # 수정본: config.py의 검색 K값 적용
    docs = vector_db.similarity_search(refined_query, k=Settings.VECTOR_SEARCH_K)
    
    context_list = []
    sources = []
    root_folder_name = "@@@인도네시아PDT암센터FS"
    
    for d in docs:
        content = d.page_content
        
        # 1. 본문 안에 "Source:"라는 단어가 포함되어 있는지 확인
        if "Source:" in content:
            lines = content.split('\n')
            source_line = ""
            actual_body = []
            
            for line in lines:
                if line.startswith("Source:"):
                    source_line = line.replace("Source:", "").strip()
                elif line.strip().startswith("---"): 
                    continue
                else:
                    actual_body.append(line)
            
            # 경로 간소화 처리
            if source_line:
                source_line = source_line.replace('\\', '/')
                target_root = root_folder_name.replace('\\', '/')
                
                if target_root in source_line:
                    display_path = source_line.split(target_root)[-1].lstrip('/')
                else:
                    display_path = os.path.basename(source_line)
                
                sources.append(display_path)
            
            context_list.append("\n".join(actual_body))
        else:
            # Source 문구가 없는 경우 (v3 방식 메타데이터 추출)
            context_list.append(content)
            # 원본: raw_src = d.metadata.get("source", "알 수 없음")
            # 수정본: metadata['source'] 키 확인
            raw_src = d.metadata.get("source") or d.metadata.get("file_path") or "알 수 없음"
            sources.append(os.path.basename(raw_src))
    
    sources = sorted(list(set([s for s in sources if s]))) 
    context = "\n\n".join(context_list)
    
    prompt = f"다음 문맥을 바탕으로 질문에 정확히 답하세요:\n\n{context}\n\n질문: {refined_query}"
    
    try:
        response = llm.invoke(prompt)
        answer = response.content
    except Exception as e:
        logger.error(f"LLM 호출 에러: {e}")
        answer = "답변을 생성하는 중에 오류가 발생했습니다."

    return {
        "original_text": query,
        "refined_query": refined_query,
        "answer": answer,
        "sources": sources
    }

# 3. API 엔드포인트
class ChatRequest(BaseModel):
    # 원본: message: str
    # 수정본: curl 테스트 시 'text'로 보내셨으므로 호환성 위해 message 또는 text 지원
    message: str = None
    text: str = None

@app.post("/chat")
@app.post("/query") # 추가: curl 테스트 시 사용한 /query 엔드포인트 지원
async def chat_text(request: ChatRequest):
    query_text = request.message or request.text
    if not query_text:
        raise HTTPException(status_code=400, detail="message or text is required")
    return perform_rag_search(query_text)

@app.post("/voice")
async def chat_voice(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        audio_file = io.BytesIO(audio_bytes)
        
        segments, info = stt_model.transcribe(audio_file, beam_size=5, language="ko")
        voice_text = " ".join([segment.text for segment in segments])
        
        print(f"🎙️ [STT 인식]: {voice_text}")
        return perform_rag_search(voice_text)
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
