# (단락보존 + 키워드 가중치형 + 메모리 초기화)
import os
import chromadb
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 1. 경로 및 설정
TXT_DIR = Path(r"C:/Users/USER/rag/src/data/text_converted")
DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
COLLECTION_NAME = "indonesia_pdt_docs"
OPENAI_API_KEY = "YOUR_API_KEY"

def initialize_and_load():
    # 2. 기존 DB 폴더가 있다면 삭제 (완전 초기화)
    import shutil
    if os.path.exists(DB_PATH):
        print(f"🗑️ 기존 DB 삭제 중: {DB_PATH}")
        shutil.rmtree(DB_PATH)

    # 3. 임베딩 모델 및 텍스트 스플리터 설정
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=100,
        separators=["\n\n", "\n", " ", ""]
    )

    # 4. 파일 목록 가져오기
    all_files = list(TXT_DIR.glob("*.txt"))
    print(f"🚀 총 {len(all_files)}개 파일 로드 시작...")

    # 5. 배치 처리 (메모리 보호)
    batch_size = 10 
    for i in range(0, len(all_files), batch_size):
        batch_files = all_files[i : i + batch_size]
        documents = []
        metadatas = []

        for file_path in batch_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    chunks = text_splitter.split_text(content)
                    
                    for chunk in chunks:
                        documents.append(chunk)
                        metadatas.append({"source": file_path.name})
            except Exception as e:
                print(f"❌ 파일 읽기 오류 ({file_path.name}): {e}")

        # DB에 배치 단위로 추가 및 저장
        if documents:
            vector_db = Chroma.from_texts(
                texts=documents,
                embedding=embeddings,
                metadatas=metadatas,
                persist_directory=DB_PATH,
                collection_name=COLLECTION_NAME
            )
            print(f"✅ 배치 완료: {i + len(batch_files)} / {len(all_files)}")

    print(f"🏁 모든 데이터가 {DB_PATH}에 성공적으로 저장되었습니다.")

if __name__ == "__main__":
    initialize_and_load()
