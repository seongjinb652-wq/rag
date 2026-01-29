import os
import json
import shutil
import time
import logging
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Settings  # 중앙 설정 참조

# 1. 에러 로그 설정
log_file_path = Settings.LOGS_DIR / f"loader_error_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    filename=log_file_path,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
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
    embeddings = OpenAIEmbeddings(model=Settings.EMBEDDING_MODEL)
    
    # [초기화 절차]
    if Settings.RESET_DB:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] ⚠️ [초기화 모드] 기존 데이터를 삭제합니다.")
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

    # 3. 상태 확인 (이어넣기용)
    initial_count = get_db_status(vector_db)
    processed_files = set()
    if not Settings.RESET_DB and os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            processed_files = set(json.load(f))

    # 4. 대상 파일 목록 추출
    all_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
    files_to_process = [f for f in all_files if f not in processed_files]
    total_files = len(files_to_process)
    
    print(f"\n📊 [DB 현황] 기존 데이터: {initial_count}건")
    print(f"🚀 [작업 시작] 처리 대상: {total_files}개 파일 (로그: {log_file_path.name})\n")

    # 스플리터 설정 (512 권장)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=Settings.CHUNK_SIZE,
        chunk_overlap=Settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )

    # 5. 메인 처리 루프
    total_added_chunks = 0
    batch_display_size = 20 # 20개 파일마다 보고
    
    for idx, file_name in enumerate(files_to_process, 1):
        file_path = os.path.join(input_dir, file_name)
        now_time = datetime.now().strftime("%H:%M:%S")
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
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
            metadatas = [{Settings.META_SOURCE_KEY: original_name} for _ in range(num_chunks)]

            # ---------------------------------------------------------
            # [핵심] 분할 적재 로직 - 100개씩 끊어서 전송
            # ---------------------------------------------------------
            chunk_batch_size = 100 
            for i in range(0, num_chunks, chunk_batch_size):
                batch_chunks = chunks[i : i + chunk_batch_size]
                batch_metadatas = metadatas[i : i + chunk_batch_size]
                
                success = False
                while not success:
                    try:
                        vector_db.add_texts(texts=batch_chunks, metadatas=batch_metadatas)
                        time.sleep(Settings.SLEEP_INTERVAL)
                        success = True
                    except Exception as e:
                        err_str = str(e)
                        if "429" in err_str or "Rate limit" in err_str:
                            print(f"\n[{now_time}] ⏳ [Rate Limit] 15초 대기... ({idx}/{total_files})")
                            time.sleep(15)
                        elif "400" in err_str or "max_tokens" in err_str:
                            # 100개도 크면 20개씩 더 잘게 쪼개서 재시도
                            print(f"\n[{now_time}] ⚠️ [Token Limit] {original_name} 재분할 적재 중...")
                            for j in range(0, len(batch_chunks), 20):
                                vector_db.add_texts(texts=batch_chunks[j:j+20], metadatas=batch_metadatas[j:j+20])
                                time.sleep(Settings.SLEEP_INTERVAL)
                            success = True
                        else:
                            raise e

            # 상태 업데이트
            total_added_chunks += num_chunks
            processed_files.add(file_name)
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(list(processed_files), f, ensure_ascii=False, indent=4)
            
            # 진행 보고
            if num_chunks >= 50: # 대형 파일 기준 상향
                print(f"\n[{now_time}] 🐘 [대형] ({idx}/{total_files}) {original_name} (청크: {num_chunks}개)")
            
            if idx % batch_display_size == 0:
                print(f"\n[{now_time}] 📦 [배치] {idx}/{total_files} 파일 완료 (누적 청크: {total_added_chunks})")
            else:
                print(f"\r[{now_time}] ({idx}/{total_files}) 처리 중: {original_name[:25]}...", end="")

        except Exception as e:
            err_msg = f"실패: {file_name} | 이유: {str(e)}"
            print(f"\n[{now_time}] ❌ {err_msg}")
            logging.error(err_msg)

    # 6. 최종 결과
    final_count = get_db_status(vector_db)
    print("\n\n" + "="*60)
    print("🏁 모든 데이터 적재 완료")
    print(f"📈 DB 청크 변화: {initial_count} -> {final_count} (증분: {total_added_chunks})")
    print(f"📄 에러 로그: {log_file_path}")
    print("="*60)

if __name__ == "__main__":
    process_and_save()
