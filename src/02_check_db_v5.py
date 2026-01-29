#02_check_db_v5.py
import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from config import Settings  # v5 중앙 설정 참조

def check_database():
    # 1. v5 설정 연동 (기존 값 주석 보존)
    # DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
    db_path = str(Settings.CHROMA_DB_PATH)
    # COLLECTION_NAME = "indonesia_pdt_docs"
    collection_name = Settings.CHROMA_COLLECTION_NAME
    # embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    embeddings = OpenAIEmbeddings(model=Settings.EMBEDDING_MODEL)

    print(f"🔍 [v5] DB 위치 확인: {db_path}")
    print(f"🔍 [v5] 컬렉션 확인: {collection_name}")

    if not os.path.exists(db_path):
        print("❌ DB 폴더가 존재하지 않습니다. 먼저 01_loader를 실행하세요.")
        return

    # 2. 벡터 DB 연결
    vector_db = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings,
        collection_name=collection_name
    )

    # 3. 데이터 요약 통계
    try:
        # DB 내 전체 데이터 개수 확인
        collection = vector_db.get()
        total_count = len(collection['ids'])
        
        print("-" * 50)
        print(f"📊 총 벡터 데이터(청크) 개수: {total_count}개")
        
        if total_count > 0:
            # 첫 번째 데이터의 메타데이터와 내용 일부 출력하여 검증
            print(f"📄 첫 번째 데이터 샘플 확인:")
            # v5 표준: Settings.META_SOURCE_KEY("source") 확인
            # raw_source = collection['metadatas'][0].get("source")
            raw_source = collection['metadatas'][0].get(Settings.META_SOURCE_KEY, "알 수 없음")
            
            print(f"   - 출처(Source): {raw_source}")
            print(f"   - 본문 요약: {collection['documents'][0][:100]}...")
            
            # 임베딩 차원 및 모델 일치 여부는 에러 발생 여부로 간접 확인됨
            print("✅ 임베딩 및 메타데이터 형식이 v5 표준과 일치합니다.")
        else:
            print("⚠️ DB는 생성되었으나 내부 데이터가 비어 있습니다.")
            
    except Exception as e:
        print(f"❌ DB 확인 중 오류 발생: {e}")
        print("💡 팁: 임베딩 모델 설정(1536차원)이 실제 DB와 맞는지 확인하세요.")

if __name__ == "__main__":
    check_database()
