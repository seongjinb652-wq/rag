import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

# 설정 (v4와 동일)
DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
COLLECTION_NAME = "indonesia_pdt_docs"

# 1. 엔진 준비
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_db = Chroma(
    persist_directory=DB_PATH, 
    embedding_function=embeddings,
    collection_name=COLLECTION_NAME
)

# 2. 질문 던지기 (3.2GB나 109GB에 들어있을 법한 키워드로 바꿔보세요)
query = "인도네시아 PDT 관련 주요 규정이나 핵심 내용을 알려줘"

print(f"\n🔍 질문: {query}")
print("-" * 50)

# 3. 유사한 문서 3개 찾아오기
docs = vector_db.similarity_search(query, k=3)

# 4. 결과 출력
for i, doc in enumerate(docs):
    print(f"[{i+1}] 출처: {doc.metadata.get('source', '알 수 없음')}")
    print(f"내용 요약: {doc.page_content[:200]}...")
    print("-" * 50)
