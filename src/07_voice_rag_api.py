import os
import uvicorn
import io
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from faster_whisper import WhisperModel

# 외부 사전 파일에서 함수 로드
from alias_map import clean_and_refine

# 1. 초기화 및 설정
DB_PATH = "./chroma_db"
COLLECTION_NAME = "project_docs"
app = FastAPI(title="FS Voice RAG System (large-v3)")

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

# Whisper Large-v3 모델 로드 (i7-14700 / 32GB RAM 최적화)
print("⏳ Whisper STT 엔진(Large-v3) 로딩 중... (약 3GB)")
stt_model = WhisperModel("large-v3", device="cpu", compute_type="int8")

print("✅ 엔진 준비 완료")

# 2. 공통 검색 로직
def perform_rag_search(query: str):
    refined_query = clean_and_refine(query)
    print(f"🔍 [최종 교정 쿼리]: {refined_query}")
    
    docs = vector_db.similarity_search(refined_query, k=5)
    
    context_list = []
    sources = []
    root_folder_name = "@@@인도네시아PDT암센터FS"
    
    for d in docs:
        content = d.page_content
        
        # 1. 본문 안에 "Source:"라는 단어가 포함되어 있는지 확인
        if "Source:" in content:
            # Source: 로 시작하는 줄을 정확히 찾아냄
            lines = content.split('\n')
            source_line = ""
            actual_body = []
            
            for line in lines:
                if line.startswith("Source:"):
                    source_line = line.replace("Source:", "").strip()
                elif line.strip() == "---": # 절취선 제외
                    continue
                else:
                    actual_body.append(line)
            
            # 경로 간소화 처리
            if source_line:
                if root_folder_name in source_line:
                    display_path = source_line.split(root_folder_name)[-1].lstrip('\\')
                else:
                    display_path = os.path.basename(source_line)
                sources.append(display_path)
            
            context_list.append("\n".join(actual_body))
        else:
            # Source 문구가 아예 없는 경우 기존 메타데이터 참조
            context_list.append(content)
            sources.append(d.metadata.get("source", "알 수 없음"))
    
    sources = list(set([s for s in sources if s])) # 빈 값 제외 및 중복 제거
    context = "\n".join(context_list)
    
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
        
        # Whisper 변환 (large-v3)
        segments, info = stt_model.transcribe(audio_file, beam_size=5, language="ko")
        voice_text = " ".join([segment.text for segment in segments])
        
        print(f"🎙️ [STT 인식]: {voice_text}")
        return perform_rag_search(voice_text)
    except Exception as e:
        print(f"❌ 에러 발생: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # workers=1을 지정하여 프로세스가 꼬이는 것을 방지합니다.
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
