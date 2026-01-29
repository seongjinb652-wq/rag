import os
import json
import shutil
import time
import logging
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from config import Settings  # 중앙 설정 참조 (RESET_DB 포함)

# 1. 에러 로그 설정 (logs 폴더에 일자별 기록)
log_file_path = Settings.LOGS_DIR / f"loader_error_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    filename=log_file_path,
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def get_db_status(vector_db):
    """현재 DB의 컬렉션 내 청크 개수 확인"""
    try:
        return vector_db._collection.count()
    except Exception:
        return 0

def process_and_save():
    """
    [통합 세이프 로더 v4]
    - v3 기능: Settings.RESET_DB = True 시 기존 DB 삭제 후 재시작
    - v4 기능: Settings.RESET_DB = False 시 중단된 지점부터 이어넣기
    """
    # 기본 경로 설정
    db_path = str(Settings.CHROMA_DB_PATH)
    state_file = Settings.BATCH_STATE_FILE
    input_dir = Settings.DATA_DIR / "text_converted"
    embeddings = OpenAIEmbeddings(model=Settings.EMBEDDING_MODEL)
    
    # [v3 초기화 절차]
    if Settings.RESET_DB:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] ⚠️ [v3 모드] 초기화를 위해 기존 데이터를 삭제합니다.")
        if os.path.exists(db_path):
            shutil.rmtree(db_path)
            print(f"[{now}] 🗑️  DB 폴더 삭제 완료.")
        if os.path.exists(state_file):
            os.remove(state_file)
            print(f"[{now}] 🗑️  상태 기록 파일 삭제 완료.")

    # 2. 벡터 DB 연결
    vector_db = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings,
        collection_name=Settings.CHROMA_COLLECTION_NAME
    )

    # 3. 상태 확인
    initial_count = get_db_status(vector_db)
    processed_files = set()
    if not Settings.RESET_DB and os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            processed_files = set(json.load(f))

    # 4. 대상 파일 목록 추출
    all_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
    files_to_process = [f for f in all_files if f not in processed_files]
    total_files = len(files_to_process)
    
    # 5. 통계 및 배치 관리 변수
    batch_size = 20         # 20개 파일마다 배치 보고
    current_batch_chunks = 0
    total_added_chunks = 0
    
    print(f"\n📊 [DB 현황] 기존 데이터: {initial_count}건")
    print(f"🚀 [작업 시작] 처리 대상: {total_files}개 파일 (로그: {log_file_path.name})\n")

    # 스플리터 설정 (의미 단위 분리를 위한 separators 포함)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=Settings.CHUNK_SIZE,
        chunk_overlap=Settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", " ", ""]
    )

    # 6. 메인 처리 루프
    for idx, file_name in enumerate(files_to_process, 1):
        file_path = os.path.join(input_dir, file_name)
        now_time = datetime.now().strftime("%H:%M:%S")
        
        try:
            # 파일 읽기 (인코딩 에러 무시 설정으로 안정성 확보)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                full_content = f.read()
            
            lines = full_content.split('\n')
            
            # [출처 복원] 00번 컨버터에서 넣은 "Source:" 헤더 파싱
            if lines and lines[0].startswith("Source:"):
                full_source_path = lines[0].replace("Source:", "").strip()
                original_name = full_source_path.replace('\\', '/').split('/')[-1]
                # 본문 정제: 헤더(0)와 구분선(1) 제외하고 2번 줄부터
                content_body = "\n".join(lines[2:]).strip()
            else:
                original_name = file_name.rsplit('_', 1)[0]
                content_body = full_content

           # 1. 청크 생성 
            chunks = text_splitter.split_text(content_body)
            num_chunks = len(chunks)
            metadatas = [{Settings.META_SOURCE_KEY: original_name} for _ in range(num_chunks)]

            # 2. [수정] 청크 단위 분할 적재 루프 (안정성 강화)
            # 파일이 아무리 커도 50개 청크씩 끊어서 전송합니다.
            chunk_batch_size = 50 
            
            for i in range(0, num_chunks, chunk_batch_size):
                batch_chunks = chunks[i : i + chunk_batch_size]
                batch_metadatas = metadatas[i : i + chunk_batch_size]
                
                success = False
                while not success:
                    try:
                        # 전체 chunks가 아니라 batch_chunks를 보냅니다.
                        vector_db.add_texts(texts=batch_chunks, metadatas=batch_metadatas)
                        time.sleep(Settings.SLEEP_INTERVAL) # 설정값 (0.1 등)
                        success = True
                    except Exception as e:
                        if "429" in str(e) or "Rate limit" in str(e):
                            print(f"\n[{now_time}] ⏳ [Rate Limit] 10초 대기 중... ({idx}/{total_files})")
                            time.sleep(10)
                        elif "max_tokens" in str(e):
                            # 만약 50개도 너무 크다면 (극단적인 경우) 더 쪼개거나 건너뜀
                            print(f"\n[{now_time}] ⚠️ [Token Limit] 청크 사이즈 조정이 필요할 수 있습니다.")
                            break
                        else:
                            raise e
            # [안정성 적재 루프] Rate Limit 대응
            success = False
            while not success:
                try:
                    vector_db.add_texts(texts=chunks, metadatas=metadatas)
                    time.sleep(Settings.SLEEP_INTERVAL)  # 인베딩 과부하 방지 휴식
                    success = True
                except Exception as e:
                    if "429" in str(e):
                        print(f"\n[{now_time}] ⏳ [Rate Limit] 10초 대기 후 재시도... ({idx}/{total_files})")
                        time.sleep(10)
                    else:
                        raise e # 다른 에러는 상위 except로 전달

            # 통계 업데이트 및 진행 상태 저장
            current_batch_chunks += num_chunks
            total_added_chunks += num_chunks
            processed_files.add(file_name)
            
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(list(processed_files), f, ensure_ascii=False, indent=4)
            
            # [화면 출력 로직]
            # 큰 파일(청크 20개 이상) 알림
            if num_chunks >= 20:
                print(f"\n[{now_time}] 🐘 [대형] ({idx}/{total_files}) {original_name} (청크: {num_chunks}개)")
            
            # 배치 단위 보고
            if idx % batch_size == 0:
                print(f"\n[{now_time}] 📦 [배치완료] {idx}번까지 처리 완료 (현재 배치 청크: {current_batch_chunks}개)")
                current_batch_chunks = 0
            else:
                # 일반 파일은 한 줄 갱신
                print(f"\r[{now_time}] ({idx}/{total_files}) 처리 중: {original_name[:25]}...", end="")

        except Exception as e:
            err_msg = f"실패: {file_name} | 이유: {str(e)}"
            print(f"\n[{now_time}] ❌ {err_msg}")
            logging.error(err_msg)

    # 7. 최종 결과 리포트
    final_count = get_db_status(vector_db)
    print("\n\n" + "="*60)
    print("🏁 모든 데이터 적재 완료")
    print("-" * 60)
    print(f"📅 완료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📈 DB 청크 변화: {initial_count} -> {final_count} (증분: {total_added_chunks})")
    print(f"📄 에러 로그 확인: {log_file_path}")
    
    # 마지막 데이터 샘플 검증
    try:
        sample = vector_db.get(limit=1, include=['documents', 'metadatas'])
        if sample['documents']:
            print(f"🔗 검증 출처: {sample['metadatas'][0].get(Settings.META_SOURCE_KEY)}")
            print(f"📝 내용 샘플: {sample['documents'][0][:50]}...")
    except: pass
    print("="*60)

if __name__ == "__main__":
    process_and_save()
