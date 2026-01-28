import os
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from faster_whisper import WhisperModel
import io

from alias_map import clean_and_refine

# 1. 초기화
DB_PATH = "./chroma_db"
COLLECTION_NAME = "project_docs"
app = FastAPI(title="Voice/Text Hybrid RAG API")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG 엔진 & Whisper 모델 로드 (서버 시작 시 한 번만)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_db = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME
)
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

# Whisper 모델 로드 (CPU 최적화 버전)
print("⏳ Whisper STT 엔진 로딩 중...")
stt_model = WhisperModel("base", device="cpu", compute_type="int8")
print("✅ 엔진 준비 완료")

# 2. 데이터 모델
class ChatRequest(BaseModel):
    message: str

# 3. 비즈니스 로직 (공통 검색 함수)
def perform_rag_search(query: str):
    refined_query = clean_and_refine(query)
    docs = vector_db.similarity_search(refined_query, k=5)
    context = "\n".join([d.page_content for d in docs])
    sources = list(set([d.metadata.get("source", "알 수 없음") for d in docs]))
    
    prompt = f"다음 문맥을 바탕으로 질문에 답하세요:\n\n{context}\n\n질문: {refined_query}"
    response = llm.invoke(prompt)
    
    return {
        "refined_query": refined_query,
        "answer": response.content,
        "sources": sources
    }

# 4. 엔드포인트: 텍스트 질의
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    return perform_rag_search(request.message)

# 5. 엔드포인트: 음성 질의 (Audio -> STT -> RAG)
@app.post("/voice")
async def voice_endpoint(file: UploadFile = File(...)):
    try:
        # 오디오 파일 메모리로 읽기
        audio_bytes = await file.read()
        audio_file = io.BytesIO(audio_bytes)
        
        # STT 변환 (한국어 지정)
        segments, info = stt_model.transcribe(audio_file, beam_size=5, language="ko")
        voice_text = " ".join([segment.text for segment in segments])
        
        print(f"🎙️ 인식된 음성: {voice_text}")
        
        # RAG 검색 실행
        result = perform_rag_search(voice_text)
        result["original_voice_text"] = voice_text
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
