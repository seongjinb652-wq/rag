import chromadb
from pathlib import Path

DB_PATH = Path(r"C:/Users/USER/rag/src/data/chroma_db")
COLLECTION_NAME = "indonesia_pdt_docs"

client = chromadb.PersistentClient(path=str(DB_PATH))
collection = client.get_collection(name=COLLECTION_NAME)

print(f"✅ 전체 청크 수: {collection.count()}")

# 1. 임베딩 연산 없이 데이터 '가져오기' (메모리 안전)
# 전체 데이터 중 상위 100개 내에서 표 기호가 있는 것 찾기
all_samples = collection.get(limit=100, include=['documents', 'metadatas'])

print("\n🔍 [개선된 데이터 구조 확인 - 마크다운 표 및 약어]")
print("=" * 60)

found_table = False
for i, doc in enumerate(all_samples['documents']):
    if "|" in doc: # 마크다운 표 기호가 있는지 확인
        print(f"📄 출처: {all_samples['metadatas'][i].get('source')}")
        print("-" * 30)
        print(doc) # 표 구조가 살아있는 텍스트 출력
        print("=" * 60)
        found_table = True
        break # 하나만 확인하면 되므로 중단

if not found_table:
    # 표를 못 찾았다면 첫 번째 청크라도 출력해서 'PDT(광역동 치료)' 보정 확인
    print("💡 표 기호가 포함된 청크를 못 찾아 첫 번째 청크를 출력합니다.")
    print(all_samples['documents'][0])
