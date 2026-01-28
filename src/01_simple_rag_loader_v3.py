# (단락보존 + 키워드 가중치형 + 메모리 초기화 + .env 로드)
import os
import shutil
import logging
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_chroma import Chroma
from dotenv import load_dotenv # .env 로드 함수

# .env 파일 로드
load_dotenv() 

# 이제 os.getenv를 통해 안전하게 가져옵니다.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 확인용 (키의 앞 5자리만 출력해서 잘 가져왔는지 체크)
if OPENAI_API_KEY:
    print(f"🔑 API KEY 로드 성공: {OPENAI_API_KEY[:5]}*****")
else:
    print("❌ .env 파일에서 OPENAI_API_KEY를 찾을 수 없습니다.")


# 경로 및 설정
TXT_DIR = Path(r"C:/Users/USER/rag/src/data/text_converted")
DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
COLLECTION_NAME = "indonesia_pdt_docs"

def initialize_and_load():
    # 1. DB 초기화
    if os.path.exists(DB_PATH):
        print(f"🗑️ 기존 DB 삭제 및 초기화: {DB_PATH}")
        shutil.rmtree(DB_PATH)

    # 2. 모델 및 스플리터 설정
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small") # 가성비 좋은 최신 모델
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )

    # 3. 파일 목록
    all_files = list(TXT_DIR.glob("*.txt"))
    print(f"🚀 총 {len(all_files)}개 파일 DB 적재 시작...")

    # 초기 DB 생성
    vector_db = None

    # 4. 배치 처리 (메모리 효율화)
    batch_size = 5 
    for i in range(0, len(all_files), batch_size):
        batch_files = all_files[i : i + batch_size]
        texts = []
        metadatas = []

        for file_path in batch_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    chunks = text_splitter.split_text(content)
                    for chunk in chunks:
                        texts.append(chunk)
                        metadatas.append({"source": file_path.name})
            except Exception as e:
                print(f"❌ 오류 ({file_path.name}): {e}")

        # DB에 데이터 추가
        if texts:
            if vector_db is None:
                vector_db = Chroma.from_texts(
                    texts=texts,
                    embedding=embeddings,
                    metadatas=metadatas,
                    persist_directory=DB_PATH,
                    collection_name=COLLECTION_NAME
                )
            else:
                vector_db.add_texts(texts=texts, metadatas=metadatas)
                
            vector_db.persist()  # 0.4.x 버전에서 데이터를 디스크에 즉시 쓰도록 강제함
            print(f"✅ 배치 완료: {min(i + batch_size, len(all_files))} / {len(all_files)}")

    print(f"🏁 DB 구축 완료! 위치: {DB_PATH}")

if __name__ == "__main__":
    initialize_and_load()
