
#===============================================================================
#📄 Local Batch Scheduler
#===============================================================================

#Author   : 성진
#Date     : 2026-01-26
#Purpose  : 
#    - 로컬 디렉토리(C:\Users\USER\Downloads\@@@인도네시아PDT암센터FS) 내 파일들을 
#      배치 처리하기 위한 스케줄러 프로그램
#    - Object Storage 버전(setup_batch_scheduler.py)을 로컬 환경에 맞게 단순화

#Features :
#    1. 지정된 디렉토리 하위 모든 파일 스캔
#    2. 신규/수정 파일 분류 (상태 파일 batch_state_local.json 기반)
#    3. 문서 처리기 호출 (샘플: 파일 크기 기록, 추후 LLM 연동 가능)
#    4. 처리 결과 로그 및 상태 저장

#Usage    :
#    python local_batch_scheduler.py

#Notes    :
#    - 첫 실행 시 모든 파일을 신규로 처리
#    - 이후 실행에서는 수정된 파일만 재처리
#    - 상태 파일(batch_state_local.json)을 삭제하면 전체 재처리 가능
# ===============================================================================


import os
import json
import logging
from datetime import datetime
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

STATE_FILE = Path("batch_state_local.json")
TARGET_DIR = Path(r"C:\Users\USER\Downloads\@@@인도네시아PDT암센터FS")

class LocalBatchScheduler:
    def __init__(self):
        self.state = self.load_state()

    def load_state(self):
        if STATE_FILE.exists():
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"processed_files": {}}

    def save_state(self):
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def scan_files(self):
        logger.info("🔍 로컬 디렉토리 스캔 시작...")
        files = []
        for root, _, filenames in os.walk(TARGET_DIR):
            for fname in filenames:
                full_path = Path(root) / fname
                stat = full_path.stat()
                files.append({
                    "name": fname,
                    "path": str(full_path),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        logger.info(f"✅ 스캔 완료: {len(files)}개 파일 발견")
        return files

    def classify_files(self, all_files):
        new_files, modified_files = [], []
        for f in all_files:
            key = f["path"]
            if key not in self.state["processed_files"]:
                new_files.append(f)
            else:
                prev_mtime = self.state["processed_files"][key]["modified_time"]
                if f["modified"] > prev_mtime:
                    modified_files.append(f)

        logger.info(f"📊 분류 완료: 신규 {len(new_files)}개, 수정 {len(modified_files)}개")
        return new_files, modified_files

    def process_files(self, files):
        for f in files:
            logger.info(f"📄 처리 중: {f['path']}")
            # 여기서 문서 처리기 호출 (예: 텍스트 추출, 청크 생성)
            # 샘플로 단순히 파일 크기만 기록
            self.state["processed_files"][f["path"]] = {
                "modified_time": f["modified"],
                "file_size": f["size"],
                "status": "processed"
            }

    def run(self):
        logger.info("🚀 배치 처리 시작")
        all_files = self.scan_files()
        new_files, modified_files = self.classify_files(all_files)

        if not new_files and not modified_files:
            logger.info("처리할 새 파일이나 수정 파일이 없습니다")
            return

        self.process_files(new_files + modified_files)
        self.save_state()
        logger.info("✅ 배치 처리 완료")

if __name__ == "__main__":
    scheduler = LocalBatchScheduler()
    scheduler.run()
