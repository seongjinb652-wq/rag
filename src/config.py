#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Day 1: 중앙 설정 관리
모든 프로젝트 설정을 한곳에서 관리
"""

import os
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
    # Claude API (향후 확장 가능성을 위해 주석 처리)
    # ========================
    # ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    # ANTHROPIC_MODEL = 'claude-3-5-sonnet-20241022'
    # MAX_TOKENS = 1024
    
    # ========================
    # OPENAI API
    # ========================
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = 'gpt-4o-mini'  # (저비용)    
    
    # ========================
    # 네이버 클라우드 Object Storage (향후 확장 가능성을 위해 주석 처리)
    # ========================
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
    
    # 디렉토리 자동 생성
    @staticmethod
    def init_directories():
        """필요한 디렉토리 생성"""
        for dir_path in [Settings.DATA_DIR, Settings.LOGS_DIR, Settings.DOWNLOADS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    # ========================
    # 문서 처리 설정 (Day 2+)
    # ========================
    CHUNK_SIZE = 512  # 토큰 단위
    CHUNK_OVERLAP = 50
    SUPPORTED_FORMATS = {'.pdf', '.pptx', '.docx', '.txt', '.png', '.jpg', '.jpeg'}
    
    # ========================
    # 임베딩 설정 (Day 3+)
    # ========================
    # 한국어 특화 사용 시 (768차원)
    # EMBEDDING_MODEL = 'ko-sbert-multitask'
    # EMBEDDING_DIMENSION = 768

    # 현재 2.3GB DB를 생성한 실제 모델 (384차원)
    # EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
    # EMBEDDING_DIMENSION = 384  # 모델에 맞춰 수정
    EMBEDDING_MODEL = "text-embedding-3-small"   # OpenAI 모델명  
    EMBEDDING_DIMENSION = 1536                   # OpenAI 모델의 차원수
    # --- [Case 1] 비용 0원, 내 컴퓨터 활용 (안전빵) ---
    # EMBEDDING_MODEL = "jhgan/ko-sroberta-multitask"
    # EMBEDDING_DIMENSION = 768

    # --- [Case 2] 유료지만 성능 확실 (한국어 최강) ---
    # EMBEDDING_MODEL = "upstage/solar-1-mini-embedding"
    # EMBEDDING_DIMENSION = 4096

    # --- [Case 3] 현재 설정 (주의: 대량 데이터 시 비용 발생) ---
    # EMBEDDING_MODEL = "text-embedding-3-small"    # $0.00002 ( 1k 약 27원)    2.3G 기준 2~3만원 2026.1 기준. 10억 토큰 
    # EMBEDDING_DIMENSION = 1536                    # 
    # EMBEDDING_MODEL = "text-embedding-3-large"  # 0.00013     2.3G 기준 15~16만원 2026.1 기준.
    # EMBEDDING_DIMENSION = 3072                  # 
    
    # ========================
    # 벡터 DB 설정 (Day 3+ 핵심)
    # ========================
    # 원본: CHROMA_DB_PATH = DATA_DIR / 'chroma_db'
    # 수정본: 경로의 명확성을 위해 DATA_DIR 참조 유지
    CHROMA_DB_PATH = DATA_DIR / 'chroma_db'
    # 원본: CHROMA_COLLECTION_NAME = 'rag_documents'
    CHROMA_COLLECTION_NAME = 'rag_documents'
    
    # ========================
    # 배치 설정 (Day 6+ / 보존을 위해 주석 처리)
    # ========================
    # BATCH_SCHEDULE_DAY = 1  # 매월 1일
    # BATCH_SCHEDULE_HOUR = 2  # 오전 2시
    # BATCH_SCHEDULE_MINUTE = 0
    # BATCH_STATE_FILE = DATA_DIR / 'batch_state.json'
    
    # ========================
    # Azure 설정 (Day 12+ / 보존을 위해 주석 처리)
    # ========================
    # AZURE_SUBSCRIPTION_ID = os.getenv('AZURE_SUBSCRIPTION_ID')
    # AZURE_RESOURCE_GROUP = os.getenv('AZURE_RESOURCE_GROUP', 'rag-chatbot-rg')
    # AZURE_APP_NAME = os.getenv('AZURE_APP_NAME', 'rag-chatbot-app')
    
    # ========================
    # 성능 설정
    # ========================
    API_TIMEOUT = 30  # 초
    VECTOR_SEARCH_K = 5  # 상위 5개 검색
    
    @classmethod
    def validate(cls):
        """필수 설정 검증 (미사용 항목은 주석 처리)"""
        required = {
            # 'ANTHROPIC_API_KEY': 'Claude API 키',
            # 'NAVER_ACCESS_KEY': '네이버 클라우드 Access Key',
            # 'NAVER_SECRET_KEY': '네이버 클라우드 Secret Key',
            # 'NAVER_BUCKET_NAME': '네이버 클라우드 Bucket 이름',
            'OPENAI_API_KEY': 'OpenAI API 키'
        }
        
        missing = []
        for key, desc in required.items():
            if not getattr(cls, key):
                missing.append(f"{key} ({desc})")
        
        if missing:
            raise ValueError(f"필수 설정 누락: {', '.join(missing)}")
        
        return True

# 초기화
Settings.init_directories()

if __name__ == "__main__":
    # 설정 확인 (테스트용)
    print("="*80)
    print("📋 현재 설정 확인")
    print("="*80)
    
    print(f"DEBUG: {Settings.DEBUG}")
    print(f"LOG_LEVEL: {Settings.LOG_LEVEL}")
    print(f"DATA_DIR: {Settings.DATA_DIR}")
    print(f"DOWNLOADS_DIR: {Settings.DOWNLOADS_DIR}")
    # print(f"NAVER_ENDPOINT: {Settings.NAVER_ENDPOINT}")
    # print(f"NAVER_BUCKET_NAME: {Settings.NAVER_BUCKET_NAME}")
    # print(f"ANTHROPIC_MODEL: {Settings.ANTHROPIC_MODEL}")
    print(f"EMBEDDING_MODEL: {Settings.EMBEDDING_MODEL}")
    print(f"CHROMA_COLLECTION: {Settings.CHROMA_COLLECTION_NAME}")
    
    print("\n" + "="*80)
    print("✅ 설정 로드 완료")
    print("="*80)
