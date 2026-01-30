import os
import json
import shutil
import time
import logging
import re
from datetime import datetime
# [2026-01-31 성진 추가 정의] 로컬 임베딩용 라이브러리 추가
from langchain_huggingface import HuggingFaceEmbeddings
# [기존 유지]
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Settings  # 모든 상수는 여기서 참조

# 1. 에러 로그 설정
log_file_path = Settings.LOGS_DIR / f"loader_error_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    filename=log_file_path,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding=Settings.ENCODING  # [2026-01-31 성진 변수 처리]
)

def get_db_status(vector_db):
    try:
        return vector_db._collection.count()
    except Exception:
        return 0

def process_and_save():
    db_path = str(Settings.CHROMA_DB_PATH)
    state_file = Settings.BATCH_STATE_FILE
    input_dir = Settings.DATA_DIR / "text_converted"
    
    # =========================================================
    # [2026-01-31 성진 주석 보존] 기존 OpenAIEmbeddings 설정
    # =========================================================
    # embeddings = OpenAIEmbeddings(model=Settings.EMBEDDING_MODEL)
    
    # [2026-01-31 성진 추가 정의] v5: ArtistSum 벤치마크용 로컬 모델 (상수 변수화 완료)
    print(f"🔄 로컬 임베딩 모델 로드 중: {Settings.EMBEDDING_MODEL}...")
    embeddings = HuggingFaceEmbeddings(
        model_name=Settings.EMBEDDING_MODEL,
        model_kwargs=Settings.EMBEDDING_KWARGS,
        encode_kwargs=Settings.ENCODE_KWARGS
    )
    # =========================================================
    
    # [초기화 절차]
    if Settings.RESET_DB:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] ⚠️ [v3 초기화 모드] 기존 데이터를 삭제합니다. (ArtistSum 구축)")
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
        if os.path.exists(state_file):
            os.remove(state_file)
        print(f"[{now}] 🗑️  DB 및 상태 파일 삭제 완료.")

    # 2. 벡터 DB 연결
    vector_db = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings,
        collection_name=Settings.CHROMA_COLLECTION_NAME
    )

    # 3. 상태 확인 (v4 이어넣기용)
    initial_count = get_db_status(vector_db)
    processed_files = set()
    if not Settings.RESET_DB and os.path.exists(state_file):
        with open(state_file, "r", encoding=Settings.ENCODING) as f:
            processed_files = set(json.load(f))

    # 4. 대상 파일 목록 추출
    all_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
    files_to_process = [f for f in all_files if f not in processed_files]
    total_files = len(files_to_process)
    
    print(f"\n📊 [DB 현황] 기존 데이터: {initial_count}건")
    print(f"🚀 [작업 시작] ArtistSum 처리 대상: {total_files}개 파일\n")

    # 스플리터 설정
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=Settings.CHUNK_SIZE,
        chunk_overlap=Settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )

    # 5. 메인 처리 루프
    total_added_chunks = 0
    
    for idx, file_name in enumerate(files_to_process, 1):
        file_path = os.path.join(input_dir, file_name)
        now_time = datetime.now().strftime("%H:%M:%S")
        
        try:
            with open(file_path, "r", encoding=Settings.ENCODING, errors=Settings.FILE_ERRORS_STRATEGY) as f:
                full_content = f.read()
            
            lines = full_content.split('\n')
            
            # 출처 복원 및 본문 정제
            if lines and lines[0].startswith("Source:"):
                full_source_path = lines[0].replace("Source:", "").strip()
                original_name = full_source_path.replace('\\', '/').split('/')[-1]
                content_body = "\n".join(lines[2:]).strip()
            else:
                original_name = file_name.rsplit('_', 1)[0]
                content_body = full_content

            # 청크 생성
            chunks = text_splitter.split_text(content_body)
            num_chunks = len(chunks)

            # =========================================================
            # [2026-01-31 성진 주석 보존] 기존 단일 메타데이터 설정
            # metadatas = [{Settings.META_SOURCE_KEY: original_name} for _ in range(num_chunks)]
            
            # [2026-01-31 성진 추가 정의] 확장 메타데이터 및 변수 추출 (ArtistSum 전용)
            batch_metadatas = []
            
            # [변수 처리] 실제 문서 기준 연도 추출 (추출 범위 상수화)
            doc_year = "Unknown"
            year_match = re.search(r'(19|20)\d{2}', file_name + content_body[:Settings.META_EXTRACT_LIMIT])
            if year_match:
                doc_year = year_match.group()

            for _ in range(num_chunks):
                meta = {
                    Settings.META_SOURCE_KEY: original_name,
                    Settings.META_YEAR_KEY: doc_year,
                    Settings.META_PROJECT_NAME: "ArtistSum",
                    Settings.META_DOC_TYPE: "미분류",
                    Settings.META_INDUSTRY_KEY: None,
                    Settings.META_AUTHOR_KEY: None,
                    Settings.META_TOC_KEY: None,
                    Settings.META_SECTION_KEY: None,
                    Settings.META_ANCHOR_KEY: None,
                    Settings.META_PAGE_KEY: None
                }
                batch_metadatas.append(meta)
            # =========================================================

            # ---------------------------------------------------------
            # [2026-01-31 성진 주석 보존] 원본 분할 적재 루프 및 에러 처리
            # ---------------------------------------------------------
            """
            chunk_batch_size = 100 
            for i in range(0, num_chunks, chunk_batch_size):
                # ... 기존 로직 보존 (중략) ...
            """

            # [2026-01-31 성진 추가 정의] BGE-M3 로컬 전용 고속 적재
            vector_db.add_texts(texts=chunks, metadatas=batch_metadatas)
            # ---------------------------------------------------------

            # 상태 업데이트
            total_added_chunks += num_chunks
            processed_files.add(file_name)
            with open(state_file, "w", encoding=Settings.ENCODING) as f:
                json.dump(list(processed_files), f, ensure_ascii=False, indent=4)
            
            # 디버그용 출력 제어 (상수 참조)
            if num_chunks >= Settings.LARGE_FILE_THRESHOLD: 
                print(f"\n[{now_time}] 🐘 [대형] ({idx}/{total_files}) {original_name} (청크: {num_chunks}개)")
            
            if idx % Settings.DISPLAY_INTERVAL == 0:
                print(f"\n[{now_time}] 📦 [배치] {idx}/{total_files} 완료 (누적 청크: {total_added_chunks})")
            else:
                print(f"\r[{now_time}] ({idx}/{total_files}) 처리 중: {original_name[:25]}...", end="")

        except Exception as e:
            err_msg = f"실패: {file_name} | 이유: {str(e)}"
            print(f"\n[{now_time}] ❌ {err_msg}")
            logging.error(err_msg)

    # 6. 최종 결과
    final_count = get_db_status(vector_db)
    print("\n\n" + "="*60)
    print(f"🏁 ArtistSum 모든 데이터 적재 완료 (BGE-M3 768dim)")
    print(f"📈 DB 청크 변화: {initial_count} -> {final_count} (증분: {total_added_chunks})")
    print(f"📄 에러 로그: {log_file_path.name}")
    print("="*60)

if __name__ == "__main__":
    process_and_save()
