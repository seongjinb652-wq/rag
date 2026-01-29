# (단락보존 + 키워드 가중치형 + 메모리 초기화 + .env 로드)
import os
import shutil
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from config import Settings  # 중앙 설정 참조

def process_and_save():
    # 1. DB 및 모델 설정 (기존 값 주석 보존)
    # DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
    db_path = str(Settings.CHROMA_DB_PATH)
    # COLLECTION_NAME = "indonesia_pdt_docs"
    collection_name = Settings.CHROMA_COLLECTION_NAME
    # embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    embeddings = OpenAIEmbeddings(model=Settings.EMBEDDING_MODEL)

    # [v3 원칙: 초기화] 기존 DB 폴더가 있다면 삭제하여 깨끗하게 시작
    if os.path.exists(db_path):
        print(f"🗑️ 기존 DB 초기화 중... ({db_path})")
        shutil.rmtree(db_path)

    # 2. 텍스트 분할 설정 (기존 값 주석 보존)
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=Settings.CHUNK_SIZE,
        chunk_overlap=Settings.CHUNK_OVERLAP
    )

    # 3. 신규 벡터 DB 생성
    vector_db = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings,
        collection_name=collection_name
    )

    # 4. 작업 대상 파일 목록
    input_dir = Settings.DATA_DIR / "text_converted"
    all_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
    
    print(f"🚀 총 {len(all_files)}개 파일 적재 시작 (초기화 v3 모드)")

    for file_name in all_files:
        file_path = os.path.join(input_dir, file_name)
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            raw_docs = loader.load()
            
            # [지시사항 반영] 본문 첫 줄에서 원본 파일명 추출 및 본문 정제
            for doc in raw_docs:
                lines = doc.page_content.split('\n')
                
                if lines and lines[0].startswith("Source:"):
                    # 1) 원본 경로 추출 및 OS 통합 대응 (윈도우/맥)
                    full_source_path = lines[0].replace("Source:", "").strip()
                    unified_path = full_source_path.replace('\\', '/')
                    # 2) 파일명(확장자 포함)만 추출
                    original_name = unified_path.split('/')[-1]
                    
                    # 3) 본문 정제: Source줄과 구분선 제거 (2행부터 본문 시작)
                    doc.page_content = "\n".join(lines[2:]).strip()
                else:
                    # 예외 발생 시 txt 파일명에서 해시 제거하여 사용
                    original_name = file_name.rsplit('_', 1)[0]
                
                # 4) 메타데이터에 원본 파일명(.pdf 등) 기록
                # doc.metadata["source"] = file_path
                doc.metadata[Settings.META_SOURCE_KEY] = original_name
            
            # 청크 분할 및 적재
            final_chunks = text_splitter.split_documents(raw_docs)
            vector_db.add_documents(final_chunks)
            print(f"✅ 적재 완료: {original_name}")

        except Exception as e:
            print(f"❌ 오류 발생 ({file_name}): {e}")

if __name__ == "__main__":
    process_and_save()
