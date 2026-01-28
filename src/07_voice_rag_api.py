import os
import uvicorn
import io
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from faster_whisper import WhisperModel

from alias_map import clean_and_refine

# 1. 초기화 및 설정
DB_PATH = "./chroma_db"
COLLECTION_NAME = "project_docs"
app = FastAPI(title="FS Voice RAG System (Medium)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG 컴포넌트 로드
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_db = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME
)
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

# Whisper Medium 모델 로드 (인식률 대폭 향상)
print("⏳ Whisper STT 엔진(Medium) 로딩 중... (최초 실행 시 다운로드)")
stt_model = WhisperModel("medium", device="cpu", compute_type="int8")
print("✅ 엔진 준비 완료")

# 2. 공통 검색 로직
def perform_rag_search(query: str):
    refined_query = clean_and_refine(query)
    
    # 검색 (k=5)
    docs = vector_db.similarity_search(refined_query, k=5)
    context = "\n".join([d.page_content for d in docs])
    sources = list(set([d.metadata.get("source", "알 수 없음") for d in docs]))
    
    # 답변 생성
    prompt = f"다음 문맥을 바탕으로 질문에 정확히 답하세요:\n\n{context}\n\n질문: {refined_query}"
    response = llm.invoke(prompt)
    
    return {
        "original_text": query,
        "refined_query": refined_query,
        "answer": response.content,
        "sources": sources
    }

# 3. API 엔드포인트
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_text(request: ChatRequest):
    return perform_rag_search(request.message)

@app.post("/voice")
async def chat_voice(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        audio_file = io.BytesIO(audio_bytes)
        
        # Whisper 변환
        segments, info = stt_model.transcribe(audio_file, beam_size=5, language="ko")
        voice_text = " ".join([segment.text for segment in segments])
        
        print(f"🎙️ [STT 인식]: {voice_text}")
        return perform_rag_search(voice_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
