#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Day 1: 중앙 설정 관리 (Standardized for v4)
모든 프로젝트 설정을 한곳에서 관리
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / 'data'
LOGS_DIR = PROJECT_ROOT / 'logs'
DOWNLOADS_DIR = DATA_DIR / 'downloads'

# .env 로드
load_dotenv(PROJECT_ROOT / '.env')
load_dotenv()

class Settings:
    """애플리케이션 설정"""
    
    # ========================
    # Python 환경
    # ========================
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # ========================
    # Claude API (비활성 - 주석 처리)
    # ========================
    # # 원본
    # ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    # ANTHROPIC_MODEL = 'claude-3-5-sonnet-20241022'
    # MAX_TOKENS = 1024
    
    # ========================
    # OPENAI API
    # ========================
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = 'gpt-4o-mini'
    
    # ========================
    # 네이버 클라우드 (비활성 - 주석 처리)
    # ========================
    # # 원본
    # NAVER_ENDPOINT = 'https://kr.object.ncloudstorage.com'
    # NAVER_REGION = os.getenv('NAVER_REGION', 'kr-standard')
    # NAVER_ACCESS_KEY = os.getenv('NAVER_ACCESS_KEY')
    # NAVER_SECRET_KEY = os.getenv('NAVER_SECRET_KEY')
    # NAVER_BUCKET_NAME = os.getenv('NAVER_BUCKET_NAME')
    
    # ========================
    # 디렉토리
    # ========================
    DATA_DIR = DATA_DIR
    LOGS_DIR = LOGS_DIR
    DOWNLOADS_DIR = DOWNLOADS_DIR
    
    @staticmethod
    def init_directories():
        """필요한 디렉토리 생성"""
        for dir_path in [Settings.DATA_DIR, Settings.LOGS_DIR, Settings.DOWNLOADS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # ========================
    # 문서 처리 설정
    # ========================
    CHUNK_SIZE = 512
    CHUNK_OVERLAP = 50
    SUPPORTED_FORMATS = {'.pdf', '.pptx', '.docx', '.txt', '.png', '.jpg', '.jpeg'}
    
    # ========================
    # 임베딩 설정 (Day 3+ 기준 고정)
    # ========================
    # # 원본: EMBEDDING_MODEL = 'sentence-transformers/xlm-r-base-multilingual-nli-stsb'
    EMBEDDING_DIMENSION = 768
    # # 수정본: 현재 2.3GB DB를 생성한 실제 모델
    EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
    
    # ========================
    # 벡터 DB 설정 (Day 3+ 핵심)
    # ========================
    # # 원본: CHROMA_DB_PATH = DATA_DIR / 'chroma_db'
    # # 수정본: 절대 경로 확보를 위해 확실히 정의
    CHROMA_DB_PATH = PROJECT_ROOT / 'data' / 'chroma_db'
    
    # # 원본: CHROMA_COLLECTION_NAME = 'rag_documents'
    # # 수정본: 2.3GB 데이터가 실제로 쌓인 컬렉션 이름 확인
    CHROMA_COLLECTION_NAME = 'rag_documents'
    
    # ========================
    # 배치 및 기타 (필요시 유지)
    # ========================
    BATCH_STATE_FILE = DATA_DIR / 'batch_state.json'
    VECTOR_SEARCH_K = 5
    API_TIMEOUT = 30

    @classmethod
    def validate(cls):
        """필수 설정 검증 (현재 활성화된 항목만)"""
        # OpenAI 위주로 검증 변경
        if not cls.OPENAI_API_KEY:
             raise ValueError("필수 설정 누락: OPENAI_API_KEY")
        return True

# 초기화 실행
Settings.init_directories()

if __name__ == "__main__":
    print("="*80)
    print("📋 [v4] 업데이트된 설정 확인")
    print("="*80)
    print(f"CHROMA_PATH: {Settings.CHROMA_DB_PATH}")
    print(f"COLLECTION:  {Settings.CHROMA_COLLECTION_NAME}")
    print(f"MODEL:       {Settings.EMBEDDING_MODEL}")
    print("="*80)
