#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
📄 Local Batch Scheduler v3
===============================================================================

Author   : USER
Date     : 2026-01-26
Purpose  : 
    - 로컬 디렉토리(C:/Users/USER/Downloads/@@@인도네시아PDT암센터FS) 내 파일들을 
      배치 처리하기 위한 스케줄러 프로그램
    - Object Storage 버전(setup_batch_scheduler.py)을 로컬 환경에 맞게 단순화
    - 로그 파일(batch.log)과 리포트(batch_report_xxx.txt)까지 생성

Features :
    1. 지정된 디렉토리 하위 모든 파일 스캔
    2. 신규/수정 파일 분류 (상태 파일 batch_state_local.json 기반)
    3. 문서 처리기 호출 (샘플: 파일 크기 기록, 추후 LLM 연동 가능)
    4. 처리 결과 로그 및 상태 저장
    5. 최종 리포트 파일 생성

Usage    :
    python local_batch_scheduler_v3.py

Notes    :
    - 첫 실행 시 모든 파일을 신규로 처리
    - 이후 실행에서는 수정된 파일만 재처리
    - 상태 파일(batch_state_local.json)을 삭제하면 전체 재처리 가능
===============================================================================
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from config_local import Settings

# 로그 디렉토리 생성
Settings.LOG_DIR.mkdir(exist_ok=True)

# 로그 파일 이름
log_file = Settings.LOG_DIR / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# 로깅 설정 (콘솔 + 파일)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LocalBatchScheduler:
    def __init__(self):
        self.state_file = Settings.STATE_FILE
        self.target_dir = Settings.TARGET_DIR
        self.state = self.load_state()

    def load_state(self):
        if self.state_file.exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"processed_files": {}}

    def save_state(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)
        logger.info(f"✅ 상태 저장: {self.state_file}")

    def scan_files(self):
        logger.info("🔍 로컬 디렉토리 스캔 시작...")
        files = []
        for root, _, filenames in os.walk(self.target_dir):
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
            # 샘플 처리: 파일 크기만 기록
            self.state["processed_files"][f["path"]] = {
                "modified_time": f["modified"],
                "file_size": f["size"],
                "status": "processed"
            }

    def save_report(self, scanned, new, modified, deleted):
        report_file = Settings.LOG_DIR / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("================================================================================\n")
            f.write("📊 배치 처리 완료 리포트\n")
            f.write("================================================================================\n\n")
            f.write(f"⏱️ 실행 시간: {datetime.now().isoformat()}\n\n")
            f.write(f"📈 처리 통계:\n")
            f.write(f"   ✓ 스캔 파일: {scanned}개\n")
            f.write(f"   ✨ 신규 파일: {new}개\n")
            f.write(f"   📝 수정 파일: {modified}개\n")
            f.write(f"   ⚠️ 삭제 파일: {deleted}개\n")
            f.write("================================================================================\n")
        logger.info(f"✅ 리포트 저장: {report_file}")

    def run(self):
        logger.info("🚀 배치 처리 시작")
        all_files = self.scan_files()
        new_files, modified_files = self.classify_files(all_files)

        if not new_files and not modified_files:
            logger.info("처리할 새 파일이나 수정 파일이 없습니다")
            self.save_report(len(all_files), 0, 0, 0)
            return

        self.process_files(new_files + modified_files)
        self.save_state()
        self.save_report(len(all_files), len(new_files), len(modified_files), 0)
        logger.info("✅ 배치 처리 완료")


if __name__ == "__main__":
    scheduler = LocalBatchScheduler()
    scheduler.run()
