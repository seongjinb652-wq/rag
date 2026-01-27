import chromadb
from pathlib import Path

DB_PATH = Path(r"C:/Users/USER/rag/src/data/chroma_db")
COLLECTION_NAME = "indonesia_pdt_docs"

client = chromadb.PersistentClient(path=str(DB_PATH))
collection = client.get_collection(name=COLLECTION_NAME)

# 1. '부평'이 포함된 모든 메타데이터 가져오기
all_data = collection.get()
# 파일명에 '부평'이 포함된 인덱스 찾기
indices = [i for i, m in enumerate(all_data['metadatas']) if '부평' in m['source']]

if not indices:
    print("❌ DB에서 '부평' 관련 파일을 찾을 수 없습니다. 01_loader가 정상 종료되었는지 확인하세요.")
else:
    print(f"✅ 총 {len(indices)}개의 '부평' 관련 청크를 찾았습니다.")
    # 첫 5개만 출력
    for idx in indices[:5]:
        source = all_data['metadatas'][idx]['source']
        content = all_data['documents'][idx]
        print(f"\n📂 출처: {source}")
        print("-" * 50)
        print(content[:400]) # 400자 출력
        print("-" * 50)
