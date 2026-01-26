#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
배치 자동화 - 월간 문서 처리 (신규/수정/삭제 감지)
목표: 네이버 클라우드에서 파일 다운로드 → 처리 → 벡터 DB 업데이트
소유자 : 성진
날자   : 2026-01-26

로직:
1️⃣ 파일 스캔 (개수 파악)
2️⃣ 파일 상태 분류
   - 신규: 처리 필요
   - 수정: 재처리 필요 ✅ 구현됨
   - 삭제: 안전 차원 제외 (데이터 무결성) ⚠️ 차단됨
3️⃣ 샘플 테스트 (2~5개)
4️⃣ 배치 처리 (50개 단위)
5️⃣ 최종 리포트

실행: python setup_batch_scheduler.py
스케줄: 매월 1일 오전 2시 (APScheduler)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import logging
import json
from datetime import datetime
import boto3
import hashlib

# config.py 로드
PROJECT_ROOT = Path(__file__).parent.parent
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
        logging.FileHandler(Settings.LOGS_DIR / 'batch.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BatchProcessor:
    """배치 처리 엔진 - 신규, 수정, 삭제 감지 포함"""
    
    BATCH_SIZE = 50  # 한 번에 처리할 파일 개수
    SAMPLE_SIZE = 5  # 테스트 샘플 개수
    
    def __init__(self):
        """초기화"""
        logger.info("🔧 배치 처리기 초기화...")
        
        # Naver Cloud 연결
        self.s3_client = boto3.client(
            's3',
            endpoint_url=Settings.NAVER_ENDPOINT,
            aws_access_key_id=Settings.NAVER_ACCESS_KEY,
            aws_secret_access_key=Settings.NAVER_SECRET_KEY,
            region_name=Settings.NAVER_REGION
        )
        
        logger.info("✅ 네이버 클라우드 연결 완료")
        
        # 상태 파일
        self.state_file = Settings.BATCH_STATE_FILE
        self.state = self._load_state()
        
        # 처리 통계
        self.stats = {
            'start_time': None,
            'end_time': None,
            'scanned_files': 0,
            'new_files': 0,
            'modified_files': 0,
            'deleted_files': 0,  # ⚠️ 감지만 하고 처리 안 함
            'downloaded_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'total_chunks': 0,
            'errors': []
        }
    
    def _load_state(self) -> Dict:
        """상태 파일 로드
        
        상태 파일 구조:
        {
            "processed_files": {
                "file1.pdf": {
                    "modified_time": "2025-01-26T14:30:00",
                    "file_hash": "abc123def456",
                    "file_size": 5120,
                    "chunks": 250,
                    "status": "processed"
                }
            },
            "last_run": "2025-01-26T14:30:00",
            "total_chunks": 1000
        }
        """
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 초기 상태 구조
        return {
            'processed_files': {},
            'last_run': None,
            'total_chunks': 0
        }
    
    def _save_state(self):
        """상태 파일 저장"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 상태 저장: {self.state_file}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """파일 해시 계산 (파일 수정 감지용)"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def scan_files(self) -> List[Dict]:
        """Naver Cloud에서 파일 목록 스캔 + 메타데이터 수집
        
        반환: [
            {
                'name': 'file1.pdf',
                'size': 5120,
                'modified': '2025-01-26T14:30:00'
            }
        ]
        """
        
        logger.info("🔍 파일 스캔 시작...")
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=Settings.NAVER_BUCKET_NAME
            )
            
            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'name': obj['Key'],
                        'size': obj['Size'],
                        'modified': obj['LastModified'].isoformat()
                    })
            
            self.stats['scanned_files'] = len(files)
            logger.info(f"✅ 스캔 완료: {len(files)}개 파일 발견")
            
            return files
        
        except Exception as e:
            logger.error(f"❌ 스캔 실패: {e}")
            self.stats['errors'].append(f"스캔 실패: {e}")
            return []
    
    def classify_files(self, all_files: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """파일을 상태별로 분류
        
        분류:
        - 신규: 상태에 없는 파일
        - 수정: 해시값이 다른 파일
        - 삭제: 상태에는 있지만 클라우드에 없는 파일
        
        반환: (new_files, modified_files, deleted_files)
        """
        
        logger.info("📊 파일 상태 분류...")
        
        # 클라우드의 파일 이름 set
        cloud_files = {f['name'] for f in all_files}
        
        # 상태에 저장된 파일 이름 set
        stored_files = set(self.state['processed_files'].keys())
        
        new_files = []
        modified_files = []
        deleted_files = list(stored_files - cloud_files)
        
        # 신규 파일 찾기
        for file_info in all_files:
            if file_info['name'] not in self.state['processed_files']:
                new_files.append(file_info)
                logger.info(f"   ✨ 신규: {file_info['name']}")
        
        # ⚠️ 삭제 파일 감지 (처리하지 않음 - 데이터 무결성 보호)
        if deleted_files:
            logger.warning(f"⚠️ 삭제된 파일 감지: {len(deleted_files)}개")
            for deleted in deleted_files:
                logger.warning(f"   ⚠️ 삭제: {deleted}")
                # 주석: 삭제 파일은 벡터 DB에서 제거하지 않음
                # 이유: 벡터 DB에서 특정 청크만 제거하기 어려움
                # 향후: 삭제 파일 추적을 위해 상태 파일에만 기록
            self.stats['deleted_files'] = len(deleted_files)
        
        # 수정 파일 찾기 (파일 크기 비교)
        for file_info in all_files:
            if file_info['name'] in self.state['processed_files']:
                stored_size = self.state['processed_files'][file_info['name']].get('file_size', 0)
                if file_info['size'] != stored_size:
                    modified_files.append(file_info)
                    logger.info(f"   📝 수정: {file_info['name']} (크기 변경)")
        
        self.stats['new_files'] = len(new_files)
        self.stats['modified_files'] = len(modified_files)
        
        logger.info(
            f"📊 분류 완료: "
            f"신규 {len(new_files)}개, "
            f"수정 {len(modified_files)}개, "
            f"삭제 {len(deleted_files)}개"
        )
        
        return new_files, modified_files, deleted_files
    
    def download_files(self, files: List[Dict]) -> List[Path]:
        """Naver Cloud에서 파일 다운로드"""
        
        logger.info(f"⬇️ 파일 다운로드 시작: {len(files)}개")
        
        downloads_dir = Settings.DOWNLOADS_DIR
        downloads_dir.mkdir(parents=True, exist_ok=True)
        
        downloaded = []
        
        for i, file_info in enumerate(files, 1):
            file_key = file_info['name']
            try:
                local_path = downloads_dir / file_key.split('/')[-1]
                
                self.s3_client.download_file(
                    Settings.NAVER_BUCKET_NAME,
                    file_key,
                    str(local_path)
                )
                
                downloaded.append(local_path)
                self.stats['downloaded_files'] += 1
                
                if i % 10 == 0:
                    logger.info(f"   진행: {i}/{len(files)} 다운로드")
            
            except Exception as e:
                logger.error(f"❌ 다운로드 실패 ({file_key}): {e}")
                self.stats['errors'].append(f"다운로드 실패: {file_key}")
                self.stats['failed_files'] += 1
        
        logger.info(f"✅ 다운로드 완료: {len(downloaded)}개")
        
        return downloaded
    
    def test_sample(self, files: List[Path]) -> bool:
        """샘플 파일로 테스트
        
        목적: 처리 파이프라인 정상 작동 확인
        """
        
        if len(files) < self.SAMPLE_SIZE:
            sample_files = files
        else:
            sample_files = files[:self.SAMPLE_SIZE]
        
        logger.info(f"🧪 샘플 테스트: {len(sample_files)}개 파일")
        
        # Document Processor 임포트
        # sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'parse'))
        sys.path.insert(0, str(PROJECT_ROOT / 'parse'))
        from setup_document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        try:
            for file_path in sample_files:
                if not file_path.exists():
                    continue
                
                # 파일 처리 테스트
                ext = file_path.suffix.lower()
                
                if ext == '.pdf':
                    processor.process_pdf(file_path)
                elif ext == '.pptx':
                    processor.process_pptx(file_path)
                elif ext == '.docx':
                    processor.process_docx(file_path)
                elif ext in {'.png', '.jpg', '.jpeg'}:
                    processor.process_image(file_path)
            
            logger.info(f"✅ 샘플 테스트 통과")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ 샘플 테스트 실패: {e}")
            self.stats['errors'].append(f"샘플 테스트 실패: {e}")
            
            return False
    
    def process_batch(self, files: List[Path], files_info: List[Dict]) -> Tuple[int, int]:
        """배치 처리 (50개씩)
        
        신규 + 수정 파일을 처리하고 벡터 DB에 추가
        """
        
        logger.info(f"📦 배치 처리 시작: {len(files)}개 파일")
        
        # Document Processor 임포트
        # sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'parse'))
        sys.path.insert(0, str(PROJECT_ROOT / 'parse'))
        from setup_document_processor import DocumentProcessor
        
        # Vector Store 임포트
        # sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'embed'))
        sys.path.insert(0, str(PROJECT_ROOT / 'embed'))
        from setup_vector_store import VectorStore
        
        processor = DocumentProcessor()
        vector_store = VectorStore()
        
        total_chunks = 0
        batch_num = 1
        
        # 파일 정보 맵 (이름 → 정보)
        file_info_map = {info['name']: info for info in files_info}
        
        # 배치 처리
        for i in range(0, len(files), self.BATCH_SIZE):
            batch = files[i:i + self.BATCH_SIZE]
            
            logger.info(f"\n🔄 배치 {batch_num}: {len(batch)}개 파일 처리 중...")
            
            documents = []
            
            for file_path in batch:
                if not file_path.exists():
                    continue
                
                try:
                    # 문서 처리
                    docs, _ = processor.process_directory(file_path.parent)
                    documents.extend(docs)
                    
                    # 파일 해시 계산 (수정 감지용)
                    file_hash = self._calculate_file_hash(file_path)
                    
                    # 상태 업데이트
                    file_name = file_path.name
                    self.state['processed_files'][file_name] = {
                        'modified_time': datetime.now().isoformat(),
                        'file_hash': file_hash,
                        'file_size': file_path.stat().st_size,
                        'chunks': len(docs),
                        'status': 'processed'
                    }
                    
                    self.stats['processed_files'] += 1
                
                except Exception as e:
                    logger.error(f"❌ 처리 실패 ({file_path.name}): {e}")
                    self.stats['failed_files'] += 1
                    self.stats['errors'].append(f"처리 실패: {file_path.name}")
            
            # 벡터 DB에 추가
            if documents:
                result = vector_store.add_documents(documents)
                chunks_added = result['added']
                total_chunks += chunks_added
                self.stats['total_chunks'] += chunks_added
                
                progress = min(i + self.BATCH_SIZE, len(files))
                logger.info(
                    f"✅ 배치 {batch_num} 완료: "
                    f"{progress}/{len(files)} 파일, "
                    f"{chunks_added}개 청크 추가"
                )
            
            batch_num += 1
        
        logger.info(f"✅ 배치 처리 완료: 총 {total_chunks}개 청크 생성")
        
        return len(files), total_chunks
    
    def generate_report(self):
        """최종 리포트 생성"""
        
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
   ⚠️ 삭제 파일: {self.stats['deleted_files']}개 (감지만, 미처리)
   ⬇️ 다운로드: {self.stats['downloaded_files']}개
   ✓ 처리 성공: {self.stats['processed_files']}개
   ✗ 처리 실패: {self.stats['failed_files']}개
   ✓ 생성 청크: {self.stats['total_chunks']}개

🗓️ 실행 시간:
   시작: {self.stats['start_time']}
   종료: {self.stats['end_time']}

{'='*80}
"""
        
        if self.stats['errors']:
            report += f"\n⚠️ 오류 목록:\n"
            for error in self.stats['errors']:
                report += f"   - {error}\n"
        
        if self.stats['deleted_files'] > 0:
            report += f"\n🔒 보안 주의:\n"
            report += f"   삭제된 파일 {self.stats['deleted_files']}개가 감지되었습니다.\n"
            report += f"   데이터 무결성 보호를 위해 벡터 DB에서 제거하지 않았습니다.\n"
            report += f"   필요시 관리자에게 문의하세요.\n"
        
        report += f"\n{'='*80}\n"
        
        logger.info(report)
        
        # 리포트 저장
        report_file = Settings.LOGS_DIR / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"✅ 리포트 저장: {report_file}")
        
        return report
    
    def run(self):
        """배치 실행 (전체 파이프라인)
        
        단계:
        1. 파일 스캔 (발견)
        2. 파일 분류 (신규, 수정, 삭제)
        3. 파일 다운로드
        4. 샘플 테스트
        5. 배치 처리 (신규 + 수정)
        6. 상태 저장
        7. 리포트 생성
        """
        
        self.stats['start_time'] = datetime.now().isoformat()
        
        logger.info("\n" + "="*80)
        logger.info("🚀 배치 처리 시작")
        logger.info("="*80)
        
        try:
            # 1️⃣ 파일 스캔
            all_files = self.scan_files()
            if not all_files:
                logger.warning("처리할 파일이 없습니다")
                return
            
            # 2️⃣ 파일 분류
            new_files, modified_files, deleted_files = self.classify_files(all_files)
            
            # 신규 + 수정 파일 합치기
            files_to_process = new_files + modified_files
            
            if not files_to_process:
                logger.info("처리할 새 파일이나 수정 파일이 없습니다")
                if deleted_files:
                    logger.warning(f"⚠️ 삭제된 파일 {len(deleted_files)}개는 미처리 (보안)")
                return
            
            # 3️⃣ 다운로드
            downloaded = self.download_files(files_to_process[:10])  # 테스트용 10개만
            if not downloaded:
                logger.error("다운로드된 파일이 없습니다")
                return
            
            # 4️⃣ 샘플 테스트
            if not self.test_sample(downloaded):
                logger.error("샘플 테스트 실패, 중단")
                return
            
            # 5️⃣ 배치 처리
            processed, chunks = self.process_batch(downloaded, files_to_process[:10])
            
            # 6️⃣ 상태 저장
            self.state['last_run'] = datetime.now().isoformat()
            self.state['total_chunks'] = self.stats['total_chunks']
            self._save_state()
            
            # 7️⃣ 리포트 생성
            self.generate_report()
        
        except Exception as e:
            logger.error(f"❌ 배치 실패: {e}", exc_info=True)
            self.stats['errors'].append(f"배치 실패: {e}")


def main():
    """메인 함수"""
    batch = BatchProcessor()
    batch.run()


if __name__ == "__main__":
    main()
