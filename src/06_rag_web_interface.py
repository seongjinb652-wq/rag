import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from alias_map import refine_text  # 아까 만든 교정 함수

# 1. 설정 및 초기화
DB_PATH = "./chroma_db"
COLLECTION_NAME = "project_docs"

app = FastAPI(title="FS Project RAG API")

# React 연동을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 개발 시에는 모두 허용
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG 엔진 준비 (05번에서 검증된 설정 그대로 사용)
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_db = Chroma(
    persist_directory=DB_PATH,
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME
)
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

# 2. 데이터 모델
class ChatRequest(BaseModel):
    message: str

# 3. 비즈니스 로직: 검색 및 답변
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # A. 질의 정제 (alias_map 적용)
        refined_query = refine_text(request.message)
        
        # B. 문서 검색 (유사도 높은 5개 유닛 추출)
        # 출처 정보를 같이 가져오기 위해 직접 검색
        docs = vector_db.similarity_search(refined_query, k=5)
        
        # C. 답변 생성 (간결한 프롬프트는 08에서 보완 예정이므로 기본형 사용)
        context = "\n".join([d.page_content for d in docs])
        sources = list(set([d.metadata.get("source", "알 수 없음") for d in docs]))
        
        # LLM 질문 (기본형)
        prompt = f"다음 문맥을 바탕으로 질문에 답하세요:\n\n{context}\n\n질문: {refined_query}"
        response = llm.invoke(prompt)
        
        return {
            "original_query": request.message,
            "refined_query": refined_query,
            "answer": response.content,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
