import os
import logging
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# 경로 및 설정
TXT_DIR = Path(r"C:/Users/USER/rag/src/data/text_converted")
DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
COLLECTION_NAME = "indonesia_pdt_docs"

def load_incremental():
    # 1. 초기화(shutil.rmtree) 로직 삭제 -> 기존 DB 유지
    if not os.path.exists(DB_PATH):
        print(f"📂 DB가 존재하지 않아 새로 생성합니다: {DB_PATH}")
    else:
        print(f"📚 기존 DB에 데이터를 이어 씁니다: {DB_PATH}")

    # 2. 모델 및 스플리터 설정
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )

    # 3. 파일 목록 (중복 적재 방지를 위해 고민이 필요하지만, 일단 전체 로드)
    all_files = list(TXT_DIR.glob("*.txt"))
    print(f"🚀 총 {len(all_files)}개 파일 처리 시작 (기존 데이터 유지)...")

    # 4. Chroma DB 연결 (기존 경로 로드)
    vector_db = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )

    # 5. 배치 처리
    batch_size = 20 
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

        if texts:
            vector_db.add_texts(texts=texts, metadatas=metadatas)
            print(f"✅ 배치 완료: {min(i + batch_size, len(all_files))} / {len(all_files)}")

    print(f"🏁 증분 적재 완료! 위치: {DB_PATH}")

if __name__ == "__main__":
    load_incremental()
