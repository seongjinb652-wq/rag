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

            # 청크 생성
            chunks = text_splitter.split_text(content_body)
            num_chunks = len(chunks)
            metadatas = [{Settings.META_SOURCE_KEY: original_name} for _ in range(num_chunks)]

            # [안정성 적재 루프] Rate Limit 대응
            success = False
            while not success:
                try:
                    vector_db.add_texts(texts=chunks, metadatas=metadatas)
                    time.sleep(0.2)  # 인베딩 과부하 방지 휴식
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
            print(f"📝 내용 샘플: {sample['documents'][0][:50].replace('\n', ' ')}...")
    except: pass
    print("="*60)

if __name__ == "__main__":
    process_and_save()import os
import json
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

    # 2. 텍스트 분할 설정 (기존 값 주석 보존)
    # text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=Settings.CHUNK_SIZE,
        chunk_overlap=Settings.CHUNK_OVERLAP
    )

    # 3. 벡터 DB 초기화/연결
    vector_db = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings,
        collection_name=collection_name
    )

    # 4. 작업 대상 파일 목록 (config의 DATA_DIR 내 text_converted 폴더 기준)
    input_dir = Settings.DATA_DIR / "text_converted"
    # state_file = "batch_state.json"
    state_file = Settings.BATCH_STATE_FILE

    # v4 이어넣기 상태 로드
    processed_files = set()
    if os.path.exists(state_file):
        with open(state_file, "r", encoding="utf-8") as f:
            processed_files = set(json.load(f))

    all_files = [f for f in os.listdir(input_dir) if f.endswith(".txt")]
    
    for file_name in all_files:
        if file_name in processed_files:
            continue
            
        file_path = os.path.join(input_dir, file_name)
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            raw_docs = loader.load()
            
            for doc in raw_docs:
                # 1. 문서 전체 내용을 줄 단위로 분리
                lines = doc.page_content.split('\n')
                first_line = lines[0].strip() # 첫 줄 추출
                
                # 2. "Source:" 문구가 있는지 확인하고 파싱
                if first_line.startswith("Source:"):
                    # "Source:" 글자 자체를 걷어내고 경로만 남김
                    full_path = first_line.replace("Source:", "").strip()
                    
                    # 3. [OS 통합] 윈도우(\)와 맥(/) 경로 구분자를 /로 통일하여 마지막 파일명 추출
                    # 이렇게 해야 '...제안 요약 - 20241226-2-1.pdf' 전체가 잡힙니다.
                    unified_path = full_path.replace('\\', '/')
                    original_name = unified_path.split('/')[-1]
                    
                    # 4. 본문 정제: 첫 줄(Source)과 그 다음 구분선(---)까지 제거
                    # 보통 0, 1번 줄이 메타데이터이므로 2번 줄부터 본문으로 사용
                    doc.page_content = "\n".join(lines[2:]).strip()
                else:
                    # 만약 첫 줄에 Source가 없다면, 차선책으로 txt 파일명에서 해시 제거
                    original_name = file_name.rsplit('_', 1)[0] + ".pdf" # 확장자 강제 부여

                # 5. 최종 결정된 '원본명.pdf'를 메타데이터에 주입
                doc.metadata[Settings.META_SOURCE_KEY] = original_name
            
            # 청크 분할 및 저장
            final_chunks = text_splitter.split_documents(raw_docs)
            vector_db.add_documents(final_chunks)
            
            # 진행 상태 기록 (v4 이어넣기)
            processed_files.add(file_name)
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(list(processed_files), f, ensure_ascii=False, indent=4)
            
            print(f"✅ 적재 완료: {file_name}")

        except Exception as e:
            print(f"❌ 오류 발생 ({file_name}): {e}")

if __name__ == "__main__":
    process_and_save()
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
