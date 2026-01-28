import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# .env 로드
load_dotenv()

DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
COLLECTION_NAME = "indonesia_pdt_docs"

def check_db_health():
    print(f"🧐 DB 상태 점검 시작: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("❌ DB 폴더가 존재하지 않습니다!")
        return

    try:
        # 1. DB 연결 (차원 확인을 위해 임베딩 모델 설정)
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        vector_db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )

        # 2. 총 데이터(Chunk) 개수 확인
        collection = vector_db._collection
        count = collection.count()
        print(f"📊 총 저장된 텍스트 조각(Chunk) 개수: {count}개")

        if count == 0:
            print("⚠️ DB가 비어있습니다. 적재 과정을 확인하세요.")
            return

        # 3. 데이터 샘플 확인 (깨짐 체크)
        sample = collection.get(limit=1)
        print("\n📄 데이터 샘플링 (첫 번째 조각):")
        print("-" * 50)
        print(f"소스 파일: {sample['metadatas'][0].get('source', '알 수 없음')}")
        print(f"내용 요약: {sample['documents'][0][:200]}...") # 앞부분 200자 출력
        print("-" * 50)

        # 4. 임베딩 모델 정보 출력
        print(f"✅ 임베딩 모델: text-embedding-3-small (1536 Dimension)")
        print("🚀 모든 체크가 완료되었습니다. 이제 검색 코드를 실행하셔도 좋습니다.")

    except Exception as e:
        print(f"❌ 점검 중 오류 발생: {e}")
        if "dimension" in str(e).lower():
            print("💡 경고: DB 내 임베딩 차원이 일치하지 않습니다. v3(초기화) 적재가 필요할 수 있습니다.")

if __name__ == "__main__":
    check_db_health()
