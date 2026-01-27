import chromadb
from pathlib import Path

DB_PATH = Path(r"C:/Users/USER/rag/src/data/chroma_db")
COLLECTION_NAME = "indonesia_pdt_docs"

client = chromadb.PersistentClient(path=str(DB_PATH))
collection = client.get_collection(name=COLLECTION_NAME)

# 특정 파일 이름이 포함된 데이터만 검색 (최대 5개 청크)
results = collection.get(
    where={"source": "[kisrating}부평주상복합_2015.7.8(효성).pdf"},
    limit=5
)

print(f"\n📂 파일명: {results['metadatas'][0]['source']}")
print("="*50)
for i, doc in enumerate(results['documents']):
    print(f"\n[청크 {i+1}] 미리보기:")
    print(doc[:300]) # 앞부분 300자만 출력
    print("-" * 30)
