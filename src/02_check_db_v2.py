# 마크다운 체크 포함
import chromadb
from pathlib import Path
import random

DB_PATH = Path(r"C:/Users/USER/rag/src/data/chroma_db")
COLLECTION_NAME = "indonesia_pdt_docs"

client = chromadb.PersistentClient(path=str(DB_PATH))
collection = client.get_collection(name=COLLECTION_NAME)

total_count = collection.count()
print(f"✅ 전체 청크 수: {total_count}")

if total_count > 0:
    # 1. 진짜 무작위 샘플링 (전체 ID 중 하나를 무작위로 선택)
    all_data = collection.get(include=['documents', 'metadatas'])
    all_ids = all_data['ids']
    
    random_idx = random.randint(0, total_count - 1)
    random_id = all_ids[random_idx]
    
    # 무작위 청크 1개 호출
    sample = collection.get(ids=[random_id], include=['documents', 'metadatas'])
    
    print(f"\n--- [무작위 샘플 확인] Index: {random_idx} / ID: {random_id} ---")
    print(f"📄 출처 파일: {sample['metadatas'][0].get('source')}")
    print(f"📝 내용 요약:\n{sample['documents'][0][:500]}...") # 너무 길면 잘라서 출력
    print("-" * 50)

    # 2. 표(Table) 데이터가 잘 들어갔는지 특정해서 확인
    # ' | ' 기호가 포함된 청크를 쿼리해서 표 구조 보존 여부 확인
    print("\n📊 [표 구조 보존 상태 확인]")
    table_sample = collection.query(
        query_texts=["|"], 
        n_results=1,
        include=['documents']
    )
    
    if table_sample['documents'][0]:
        print("검색된 표 데이터 일부:")
        print(table_sample['documents'][0][0])
    else:
        print("표 기호(|)를 포함한 데이터를 찾지 못했습니다. 변환 과정을 확인하세요.")
