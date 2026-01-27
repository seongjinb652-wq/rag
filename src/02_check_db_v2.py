# 마크다운 체크 포함
import chromadb
from pathlib import Path

DB_PATH = Path(r"C:/Users/USER/rag/src/data/chroma_db")
COLLECTION_NAME = "indonesia_pdt_docs"

client = chromadb.PersistentClient(path=str(DB_PATH))
collection = client.get_collection(name=COLLECTION_NAME)

print(f"✅ 전체 청크 수: {collection.count()}")

# 무작위로 1개 청크를 뽑아 '표' 구조가 살아있는지 확인
sample = collection.get(limit=1, include=['documents', 'metadatas'])
if sample['documents']:
    print("\n--- DB 적재 데이터 샘플 ---")
    print(sample['documents'][0])
    print("-" * 30)
