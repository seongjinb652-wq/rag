#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Day 1: 중앙 설정 관리 (v4 이어넣기 및 인식률 95% 최적화 버전)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# [실제 경로 계산] 이 파일의 위치를 기준으로 절대 경로 생성
PROJECT_ROOT = Path(__file__).parent.absolute()
_DATA_DIR = PROJECT_ROOT / 'data'
_LOGS_DIR = PROJECT_ROOT / 'logs'
_DOWNLOADS_DIR = _DATA_DIR / 'downloads'

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
    # OPENAI API
    # ========================
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = 'gpt-4o-mini'
    
    # ========================
    # 디렉토리 (실제 Path 객체 할당)
    # ========================
    DATA_DIR = _DATA_DIR
    LOGS_DIR = _LOGS_DIR
    DOWNLOADS_DIR = _DOWNLOADS_DIR
    
    # 디렉토리 자동 생성
    @staticmethod
    def init_directories():
        """필요한 디렉토리 생성"""
        for dir_path in [Settings.DATA_DIR, Settings.LOGS_DIR, Settings.DOWNLOADS_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

    # ========================
    # [추가] DB 처리 모드: True면 초기화(v3), False면 이어넣기(v4)
    # ========================
    RESET_DB = False
    # ========================
    # 문서 처리 설정 (1000/150 확정)
    # ========================
    CHUNK_SIZE = 1000       
    CHUNK_OVERLAP = 150     
    SUPPORTED_FORMATS = {'.pdf', '.pptx', '.docx', '.txt', '.png', '.jpg', '.jpeg'}
    
    # ========================
    # 임베딩 설정 (1536차원 확정)
    # ========================
    EMBEDDING_MODEL = "text-embedding-3-small"   
    EMBEDDING_DIMENSION = 1536                   
    
    # ========================
    # 벡터 DB 및 메타데이터 설정
    # ========================
    CHROMA_DB_PATH = _DATA_DIR / 'chroma_db'
    CHROMA_COLLECTION_NAME = 'indonesia_pdt_docs' 
    META_SOURCE_KEY = "source" 
    
    # v4 이어넣기 상태 파일 (DATA_DIR 내부 고정)
    BATCH_STATE_FILE = _DATA_DIR / 'batch_state_local.json'
    
    # ========================
    # API 및 서버 설정
    # ========================
    API_PORT = 8000
    API_BASE_URL = f"http://127.0.0.1:{API_PORT}"
    ENDPOINT_CHAT = "/chat"
    ENDPOINT_QUERY = "/query"
    ENDPOINT_VOICE = "/voice"
    
    # ========================
    # 성능 설정
    # ========================
    API_TIMEOUT = 30  
    VECTOR_SEARCH_K = 5  

    @classmethod
    def validate(cls):
        """필수 설정 검증"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("필수 설정 누락: OPENAI_API_KEY")
        return True

# 폴더 초기화 실행
Settings.init_directories()

if __name__ == "__main__":
    print("="*80)
    print(f"📂 PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"📂 DATA_DIR: {Settings.DATA_DIR}")
    print(f"📂 DB_PATH: {Settings.CHROMA_DB_PATH}")
    print(f"📂 STATE_FILE: {Settings.BATCH_STATE_FILE}")
    print("="*80)
    print("✅ 설정 및 디렉토리 준비 완료")
