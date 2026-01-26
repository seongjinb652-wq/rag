#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
로컬 배치 처리기 - 로컬 디렉토리 파일 스캔 및 처리
목표: 로컬 디렉토리 파일 → 처리 → 벡터 DB 업데이트
날짜: 2026-01-26

실행: python local_batch_scheduler_v4.py
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import logging
import json
from datetime import datetime
import hashlib

# 설정
class Settings:
    TARGET_DIR = Path(r"C:/Users/USER/Downloads/@@@인도네시아PDT암센터FS")
    STATE_FILE = Path("batch_state_local.json")
    LOG_DIR = Path("logs")
    SUPPORTED_FORMATS = {'.pdf', '.docx', '.doc', '.pptx', '.txt'}

# 로그 디렉토리 생성
Settings.LOG_DIR.mkdir(parents=True, exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Settings.LOG_DIR / 'batch.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LocalBatchProcessor:
    """로컬 배치 처리 엔진"""
    
    BATCH_SIZE = 50
    SAMPLE_SIZE = 5
    
    def __init__(self):
        logger.info("🔧 로컬 배치 처리기 초기화...")
        
        self.target_dir = Settings.TARGET_DIR
        self.state_file = Settings.STATE_FILE
        self.state = self._load_state()
        
        self.stats = {
            'start_time': None,
            'end_time': None,
            'scanned_files': 0,
            'new_files': 0,
            'modified_files': 0,
            'deleted_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'total_chunks': 0,
            'errors': []
        }
    
    def _load_state(self) -> Dict:
        """상태 파일 로드"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        return {
            'processed_files': {},
            'last_run': None,
            'total_chunks': 0
        }
    
    def _save_state(self):
        """상태 파일 저장"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 상태 저장: {self.state_file}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """파일 해시 계산"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def scan_files(self) -> List[Dict]:
        """로컬 디렉토리 재귀 스캔"""
        
        logger.info("🔍 로컬 파일 스캔 시작 (하위 디렉토리 포함)...")
        
        if not self.target_dir.exists():
            logger.error(f"❌ 디렉토리 없음: {self.target_dir}")
            return []
        
        files = []
        
        for root, dirs, filenames in os.walk(self.target_dir):
            for fname in filenames:
                file_path = Path(root) / fname
                
                # 지원 형식만
                if file_path.suffix.lower() in Settings.SUPPORTED_FORMATS:
                    try:
                        stat = file_path.stat()
                        files.append({
                            'name': fname,
                            'path': str(file_path),
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        })
                        
                        if len(files) % 100 == 0:
                            logger.info(f"   스캔 중... {len(files)}개 파일 발견")
                    
                    except Exception as e:
                        logger.warning(f"⚠️ 파일 정보 읽기 실패: {fname} - {e}")
        
        self.stats['scanned_files'] = len(files)
        logger.info(f"✅ 스캔 완료: {len(files)}개 파일 발견")
        
        # 디렉토리별 통계
        dir_counts = {}
        for file_info in files:
            dir_path = str(Path(file_info['path']).parent)
            dir_counts[dir_path] = dir_counts.get(dir_path, 0) + 1
        
        logger.info(f"📁 디렉토리별 파일 분포:")
        for dir_path, count in sorted(dir_counts.items()):
            logger.info(f"   {dir_path}: {count}개")
        
        return files
    
    def classify_files(self, all_files: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """파일 분류"""
        
        logger.info("📊 파일 상태 분류...")
        
        cloud_files = {f['path'] for f in all_files}
        stored_files = set(self.state['processed_files'].keys())
        
        new_files = []
        modified_files = []
        deleted_files = list(stored_files - cloud_files)
        
        # 신규
        for file_info in all_files:
            if file_info['path'] not in self.state['processed_files']:
                new_files.append(file_info)
                logger.info(f"   ✨ 신규: {file_info['path']}")
        
        # 삭제
        if deleted_files:
            logger.warning(f"⚠️ 삭제된 파일 감지: {len(deleted_files)}개")
            for deleted in deleted_files:
                logger.warning(f"   ⚠️ 삭제: {deleted}")
            self.stats['deleted_files'] = len(deleted_files)
        
        # 수정
        for file_info in all_files:
            if file_info['path'] in self.state['processed_files']:
                stored_size = self.state['processed_files'][file_info['path']].get('file_size', 0)
                if file_info['size'] != stored_size:
                    modified_files.append(file_info)
                    logger.info(f"   📝 수정: {file_info['path']} (크기 변경: {stored_size} → {file_info['size']})")
        
        self.stats['new_files'] = len(new_files)
        self.stats['modified_files'] = len(modified_files)
        
        logger.info(
            f"📊 분류 완료: "
            f"신규 {len(new_files)}개, "
            f"수정 {len(modified_files)}개, "
            f"삭제 {len(deleted_files)}개"
        )
        
        return new_files, modified_files, deleted_files
    
    def process_files(self, files: List[Dict]) -> int:
        """파일 처리"""
        
        logger.info(f"📦 파일 처리 시작: {len(files)}개")
        
        processed = 0
        
        for i, file_info in enumerate(files, 1):
            file_path = Path(file_info['path'])
            
            try:
                # 파일 해시 계산
                file_hash = self._calculate_file_hash(file_path)
                
                # 상태 업데이트
                self.state['processed_files'][file_info['path']] = {
                    'modified_time': file_info['modified'],
                    'file_hash': file_hash,
                    'file_size': file_info['size'],
                    'status': 'processed'
                }
                
                processed += 1
                self.stats['processed_files'] += 1
                
                if i % 10 == 0:
                    logger.info(f"   진행: {i}/{len(files)} 처리")
            
            except Exception as e:
                logger.error(f"❌ 처리 실패 ({file_info['name']}): {e}")
                self.stats['failed_files'] += 1
                self.stats['errors'].append(f"처리 실패: {file_info['name']}")
        
        logger.info(f"✅ 처리 완료: {processed}개")
        
        return processed
    
    def generate_report(self):
        """리포트 생성"""
        
        self.stats['end_time'] = datetime.now().isoformat()
        
        elapsed = (datetime.fromisoformat(self.stats['end_time']) - 
                  datetime.fromisoformat(self.stats['start_time'])).total_seconds()
        
        report = f"""
{'='*80}
📊 배치 처리 완료 리포트
{'='*80}

⏱️ 소요 시간: {elapsed:.2f}초

📈 처리 통계:
   ✓ 스캔 파일: {self.stats['scanned_files']}개
   ✨ 신규 파일: {self.stats['new_files']}개
   📝 수정 파일: {self.stats['modified_files']}개
   ⚠️ 삭제 파일: {self.stats['deleted_files']}개 (감지만)
   ✓ 처리 성공: {self.stats['processed_files']}개
   ✗ 처리 실패: {self.stats['failed_files']}개

🗓️ 실행 시간:
   시작: {self.stats['start_time']}
   종료: {self.stats['end_time']}

{'='*80}
"""
        
        if self.stats['errors']:
            report += f"\n⚠️ 오류 목록:\n"
            for error in self.stats['errors']:
                report += f"   - {error}\n"
        
        report += f"\n{'='*80}\n"
        
        logger.info(report)
        
        # 리포트 저장
        report_file = Settings.LOG_DIR / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"✅ 리포트 저장: {report_file}")
    
    def run(self):
        """배치 실행"""
        
        self.stats['start_time'] = datetime.now().isoformat()
        
        logger.info("\n" + "="*80)
        logger.info("🚀 로컬 배치 처리 시작")
        logger.info("="*80)
        
        try:
            # 1. 스캔
            all_files = self.scan_files()
            if not all_files:
                logger.warning("처리할 파일이 없습니다")
                return
            
            # 2. 분류
            new_files, modified_files, deleted_files = self.classify_files(all_files)
            
            files_to_process = new_files + modified_files
            
            if not files_to_process:
                logger.info("처리할 새 파일이나 수정 파일이 없습니다")
                if deleted_files:
                    logger.warning(f"⚠️ 삭제된 파일 {len(deleted_files)}개는 미처리")
                return
            
            # 3. 처리
            processed = self.process_files(files_to_process)
            
            # 4. 상태 저장
            self.state['last_run'] = datetime.now().isoformat()
            self._save_state()
            
            # 5. 리포트
            self.generate_report()
        
        except Exception as e:
            logger.error(f"❌ 배치 실패: {e}", exc_info=True)
            self.stats['errors'].append(f"배치 실패: {e}")


def main():
    batch = LocalBatchProcessor()
    batch.run()


if __name__ == "__main__":
    main()
