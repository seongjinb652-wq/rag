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
            lines = content.split('\n')
            source_line = ""
            actual_body = []
            
            for line in lines:
                if line.startswith("Source:"):
                    source_line = line.replace("Source:", "").strip()
                # 수정: 하이픈이 여러 개 있는 구분선(v4용)이나 '---'를 모두 건너뜀
                elif line.strip().startswith("---"): 
                    continue
                else:
                    actual_body.append(line)
            
            # 경로 간소화 처리
            if source_line:
                # v4의 슬래시(/) 경로와 v3의 역슬래시(\) 경로 모두 대응
                source_line = source_line.replace('\\', '/')
                target_root = root_folder_name.replace('\\', '/')
                
                if target_root in source_line:
                    # Root 이후의 경로만 추출
                    display_path = source_line.split(target_root)[-1].lstrip('/')
                else:
                    display_path = os.path.basename(source_line)
                
                sources.append(display_path)
            
            context_list.append("\n".join(actual_body))
        else:
            # Source 문구가 없는 옛날 데이터 처리
            context_list.append(content)
            raw_src = d.metadata.get("source", "알 수 없음")
            sources.append(os.path.basename(raw_src))
    
    # [검증 포인트 1] 중복 제거 및 정렬 (가장 깔끔한 최종 형태 하나만 남기기)
    sources = sorted(list(set([s for s in sources if s]))) 
    
    # [검증 포인트 2] 컨텍스트 결합
    context = "\n\n".join(context_list) # 문서 간 구분을 위해 \n\n 추천
    
    # [검증 포인트 3] 프롬프트 구성 및 LLM 호출
    prompt = f"다음 문맥을 바탕으로 질문에 정확히 답하세요:\n\n{context}\n\n질문: {refined_query}"
    
    try:
        response = llm.invoke(prompt)
        answer = response.content
    except Exception as e:
        logger.error(f"LLM 호출 에러: {e}")
        answer = "답변을 생성하는 중에 오류가 발생했습니다."

    # [최종 결과 반환]
    return {
        "original_text": query,
        "refined_query": refined_query,
        "answer": answer,
        "sources": sources  # 이제 리스트 형태로 정확히 나갑니다.
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
