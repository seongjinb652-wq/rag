import os
import logging
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import time

# .env 파일 로드
load_dotenv() 

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 확인용
if OPENAI_API_KEY:
    print(f"🔑 API KEY 로드 성공: {OPENAI_API_KEY[:5]}*****")
else:
    print("❌ .env 파일에서 OPENAI_API_KEY를 찾을 수 없습니다.")

# [설정] 경로는 v3와 동일하게 유지 (사용자님이 윈도우에서 파일만 교체)
TXT_DIR = Path(r"C:/Users/USER/rag/src/data/text_converted")
DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
COLLECTION_NAME = "indonesia_pdt_docs"

def append_to_existing_db():
    # 1. 모델 및 스플리터 설정 (v3와 동일하게 유지해야 데이터 일관성 보장)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )

    # 2. [v4 핵심] 기존 DB 불러오기 (삭제 로직 없음)
    if os.path.exists(DB_PATH):
        print(f"📦 기존 DB 로드 중: {DB_PATH}")
        vector_db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )
    else:
        print("❌ 기존 DB를 찾을 수 없습니다. 경로를 확인하세요.")
        return

    # 3. 새로운 파일 목록 (3.2GB 파일들이 있는 폴더)
    all_files = list(TXT_DIR.glob("*.txt"))
    print(f"🚀 총 {len(all_files)}개 파일 추가 적재 시작...")

    # 4. 배치 처리 (사용자님 최적화 설정 적용)
    batch_size = 15  # 파일 15개씩 읽기
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

        # 5. DB에 데이터 추가 (안전한 재시도 로직 포함)
        if texts:
            text_batch_limit = 100 
            for j in range(0, len(texts), text_batch_limit):
                sub_texts = texts[j : j + text_batch_limit]
                sub_metadatas = metadatas[j : j + text_batch_limit]
                
                success = False
                while not success:
                    try:
                        # add_texts를 통해 기존 컬렉션에 추가
                        vector_db.add_texts(texts=sub_texts, metadatas=sub_metadatas)
                        
                        # 사용자님 설정값: 0.2초 휴식
                        time.sleep(0.2) 
                        success = True
                    except Exception as e:
                        if "429" in str(e):
                            print("⏳ 속도 제한(429) 감지. 10초 대기 후 다시 시도합니다...")
                            time.sleep(10)
                        else:
                            print(f"❌ 데이터 추가 중 오류 발생: {e}")
                            break # 치명적 에러 시 중단
            
            print(f"✅ 추가 완료: {min(i + batch_size, len(all_files))} / {len(all_files)}")

    print(f"🏁 모든 데이터 추가 완료! 위치: {DB_PATH}")

if __name__ == "__main__":
    append_to_existing_db()
