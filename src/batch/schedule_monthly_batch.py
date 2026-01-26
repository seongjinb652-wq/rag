#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
APScheduler - 월간 자동 배치 스케줄
목표: 매월 1일 오전 2시에 자동으로 배치 처리 실행

기능:
- 배치 작업 자동 스케줄링
- 매월 1일 오전 2시 실행
- 백그라운드 프로세스 (24/7 실행)
- 실행 로그 기록
- 오류 처리 및 재시도

실행: python schedule_monthly_batch.py
(백그라운드에서 계속 실행됨 - Ctrl+C로 중단)
"""

import os
import sys
from pathlib import Path
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import time

# config.py 로드
PROJECT_ROOT = Path(__file__).parent.parent.parent
config_file = PROJECT_ROOT / 'config.py'

import importlib.util
spec = importlib.util.spec_from_file_location("config", config_file)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

Settings = config_module.Settings

# 로깅
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Settings.LOGS_DIR / 'scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MonthlyBatchScheduler:
    """월간 배치 스케줄러"""
    
    def __init__(self):
        """초기화"""
        logger.info("🔧 월간 배치 스케줄러 초기화...")
        
        # BackgroundScheduler 생성
        self.scheduler = BackgroundScheduler()
        
        # 스케줄 추가: 매월 1일 오전 2시
        # day=1: 매월 1일
        # hour=2: 오전 2시
        # minute=0: 0분
        self.scheduler.add_job(
            self.batch_job,
            trigger=CronTrigger(
                day=1,
                hour=2,
                minute=0,
                second=0
            ),
            id='monthly_batch',
            name='Monthly Batch Processing',
            misfire_grace_time=900,  # 15분 이내 놓친 작업은 실행
            coalesce=True,           # 놓친 작업을 1번만 실행
            replace_existing=True
        )
        
        logger.info("✅ 스케줄 등록 완료: 매월 1일 오전 2시")
        
        # 다음 실행 시간 표시
        self.show_next_run()
    
    def show_next_run(self):
        """다음 실행 시간 표시"""
        job = self.scheduler.get_job('monthly_batch')
        if job:
            next_run = job.next_run_time
            logger.info(f"📅 다음 실행: {next_run}")
    
    def batch_job(self):
        """배치 작업 (스케줄에서 자동 호출)
        
        매월 1일 오전 2시에 이 함수가 자동으로 실행됨
        """
        
        logger.info("\n" + "="*80)
        logger.info("🚀 스케줄된 배치 작업 시작")
        logger.info(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*80)
        
        try:
            # setup_batch_scheduler 임포트
            sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'batch'))
            from setup_batch_scheduler import BatchProcessor
            
            # 배치 처리 실행
            batch = BatchProcessor()
            batch.run()
            
            logger.info("\n" + "="*80)
            logger.info("✅ 스케줄된 배치 작업 완료")
            logger.info("="*80 + "\n")
        
        except Exception as e:
            logger.error(f"❌ 스케줄된 배치 작업 실패: {e}", exc_info=True)
    
    def start(self):
        """스케줄러 시작 (백그라운드)"""
        try:
            logger.info("\n" + "="*80)
            logger.info("🚀 APScheduler 시작")
            logger.info("="*80)
            
            self.scheduler.start()
            
            logger.info("✅ 스케줄러 백그라운드 실행 중...")
            logger.info("📌 중단하려면 Ctrl+C 눌러주세요")
            logger.info("="*80 + "\n")
            
            # 메인 스레드 유지 (무한 루프)
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("\n🛑 스케줄러 중단 요청...")
                self.shutdown()
        
        except Exception as e:
            logger.error(f"❌ 스케줄러 시작 실패: {e}", exc_info=True)
    
    def shutdown(self):
        """스케줄러 종료"""
        logger.info("🛑 스케줄러 종료 중...")
        
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("✅ 스케줄러 종료 완료")
        else:
            logger.info("스케줄러가 실행 중이 아닙니다")
    
    def list_jobs(self):
        """등록된 작업 목록 조회"""
        jobs = self.scheduler.get_jobs()
        
        logger.info("\n" + "="*80)
        logger.info("📋 등록된 작업 목록")
        logger.info("="*80)
        
        if not jobs:
            logger.info("등록된 작업이 없습니다")
        else:
            for job in jobs:
                logger.info(f"\n작업 ID: {job.id}")
                logger.info(f"  이름: {job.name}")
                logger.info(f"  실행 함수: {job.func_ref}")
                logger.info(f"  트리거: {job.trigger}")
                logger.info(f"  다음 실행: {job.next_run_time}")
        
        logger.info("="*80 + "\n")
    
    def manual_run(self):
        """수동으로 배치 작업 실행 (테스트용)"""
        logger.info("\n" + "="*80)
        logger.info("🧪 수동 배치 작업 실행 (테스트)")
        logger.info("="*80)
        
        self.batch_job()


def main():
    """메인 함수"""
    
    print("\n" + "="*80)
    print("🚀 월간 배치 스케줄러")
    print("="*80)
    print("""
옵션:
1. start    - 스케줄러 시작 (백그라운드)
2. list     - 등록된 작업 목록
3. manual   - 수동 배치 실행 (테스트)
4. help     - 도움말

예:
  python schedule_monthly_batch.py start
  python schedule_monthly_batch.py list
  python schedule_monthly_batch.py manual
""")
    print("="*80 + "\n")
    
    # 스케줄러 생성
    scheduler = MonthlyBatchScheduler()
    
    # 명령행 인자 처리
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'start':
            scheduler.start()
        
        elif command == 'list':
            scheduler.list_jobs()
        
        elif command == 'manual':
            scheduler.manual_run()
        
        elif command == 'help':
            print("""
💡 월간 배치 스케줄러 사용법

1️⃣ 스케줄러 시작 (백그라운드)
   python schedule_monthly_batch.py start
   
   효과:
   - 매월 1일 오전 2시에 자동으로 배치 처리 실행
   - 로그는 logs/scheduler.log에 기록
   - Ctrl+C로 중단 가능

2️⃣ 등록된 작업 목록 조회
   python schedule_monthly_batch.py list
   
   출력:
   - 작업 ID
   - 작업 이름
   - 트리거 조건
   - 다음 실행 시간

3️⃣ 수동 배치 실행 (테스트)
   python schedule_monthly_batch.py manual
   
   용도:
   - 스케줄러 없이 배치 실행
   - 테스트 및 검증

📅 스케줄 설정

기본값: 매월 1일 오전 2시
변경 방법:

  # 매월 15일 오전 3시로 변경
  trigger=CronTrigger(
      day=15,
      hour=3,
      minute=0
  )

⏰ Cron 표현식 예제

  day=1, hour=2, minute=0     → 매월 1일 오전 2시
  day=15, hour=3, minute=30   → 매월 15일 오전 3시 30분
  day_of_week=0, hour=6       → 매주 월요일 오전 6시
  hour=12                      → 매일 정오

🔒 Windows 백그라운드 실행

Windows에서 배치를 백그라운드로 계속 실행:

  1. 작업 스케줄러 실행
  2. 새 작업 생성
  3. 프로그램: python
  4. 인자: C:\\path\\to\\schedule_monthly_batch.py start
  5. 시작 폴더: C:\\path\\to\\

Linux/Mac 백그라운드 실행:

  nohup python schedule_monthly_batch.py start > batch_scheduler.log 2>&1 &

📊 로그 파일

  logs/scheduler.log      - 스케줄러 로그
  logs/batch.log          - 배치 처리 로그
  logs/batch_report_*.txt - 배치 리포트

🆘 트러블슈팅

Q: 스케줄러가 실행되지 않나?
A: python schedule_monthly_batch.py start 실행 후
   logs/scheduler.log에서 오류 확인

Q: 매월 1일이 아닌 특정 날에 실행하고 싶나?
A: day=15 로 변경 (day 값을 변경)

Q: 수동으로 배치를 지금 실행하고 싶나?
A: python schedule_monthly_batch.py manual

Q: 스케줄러를 종료하고 싶나?
A: Ctrl+C 누르기 (또는 Windows 작업 스케줄러에서 종료)
""")
        
        else:
            print(f"❌ 알 수 없는 명령: {command}")
            print("help 명령으로 도움말을 확인하세요")
    
    else:
        # 인자 없으면 기본: 스케줄러 시작
        print("💡 팁: python schedule_monthly_batch.py help")
        scheduler.start()


if __name__ == "__main__":
    main()
