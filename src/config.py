#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Day 1: 중앙 설정 관리 (v5: BGE-M3 768차원 및 확장 메타데이터 전략)
- v3(초기화) 및 v4(이어넣기) 히스토리 보존
- 8,020개 문서의 단계적 메타데이터(null 허용) 구축 전략 반영
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
    # [추가/수정] DB 처리 모드
    # ========================
    # RESET_DB = False  # 기존 v4 이어넣기 모드 (주석 보존)
    RESET_DB = True     # [선택] v5 신규 구축을 위한 v3 초기화 모드 가동

    # ========================
    # [추가/수정] 문서 처리 설정 (2000/200 튜닝)
    # ========================
    # CHUNK_SIZE = 1000       # 기존 1000자 (주석 보존)
    # CHUNK_OVERLAP = 150     # 기존 150자 (주석 보존)
    CHUNK_SIZE = 2000         # [추가 정의] 맥락 보존을 위한 확장
    CHUNK_OVERLAP = 200       # [추가 정의] 오버랩 확장
    
    SUPPORTED_FORMATS = {'.pdf', '.pptx', '.docx', '.txt', '.png', '.jpg', '.jpeg'}
    SLEEP_INTERVAL = 0.1

    # ========================
    # [추가/수정] 임베딩 설정 (768차원 로컬 모델)
    # ========================
    # EMBEDDING_MODEL = "text-embedding-3-small"   # 기존 OpenAI (주석 보존)
    # EMBEDDING_DIMENSION = 1536                   # 기존 1536차원 (주석 보존)
    
    # [추가 정의] BAAI/BGE-M3 무료 로컬 모델 (OpenAI Key 불필요)
    EMBEDDING_MODEL = "BAAI/bge-m3" 
    EMBEDDING_DIMENSION = 768
    EMBEDDING_DEVICE = "cuda"  # GPU 가속 사용

    # ========================
    # 벡터 DB 및 메타데이터 설정
    # ========================
    CHROMA_DB_PATH = _DATA_DIR / 'chroma_db'
    
    # [주석 보존] 기존 컬렉션명
    # CHROMA_COLLECTION_NAME = 'indonesia_pdt_docs' 
    
    # [추가 정의] v5 벤치마크용 전용 컬렉션 (768차원/2000자 명시)
    CHROMA_COLLECTION_NAME = 'as_bge_768_c2000'
    
    META_SOURCE_KEY = "source" 
    
    # ========================
    # [추가 정의] 확장 메타데이터 키 (Step 1~4 연동 및 Check DB용)
    # 초기 적재 시 값이 없으면 null(None)로라도 그릇을 생성함
    # ========================
    META_YEAR_KEY = "year"             # 연도 (필수)
    META_PROJECT_NAME = "project_name" # 프로젝트명 (필수)
    META_DOC_TYPE = "doc_type"         # 계약서/보고서/기획서 (필수)
    
    META_INDUSTRY_KEY = "industry"     # 산업군: medical, energy, infra, gov, edu, finance 등
    META_AUTHOR_KEY = "author"         # 작성자 또는 담당 부서
    
    META_TOC_KEY = "toc_title"         # Step 1~2: 목차 생성 및 검증용
    META_SECTION_KEY = "section"       # Step 3~4: 섹션별 상세 생성용
    META_ANCHOR_KEY = "anchor"         # 문서 내 절대 위치 (Page, Article, Slide 등)
    META_PAGE_KEY = "page_label"       # PDF 실제 페이지 번호
    
    # v4 이어넣기 상태 파일 및 DB 검증 리포트
    BATCH_STATE_FILE = _DATA_DIR / 'batch_state_local.json'
    DB_CHECK_REPORT_FILE = _DATA_DIR / 'db_check_report.json'
    
    # ========================
    # API 및 성능 설정
    # ========================
    API_PORT = 8000
    API_BASE_URL = f"http://127.0.0.1:{API_PORT}"
    ENDPOINT_CHAT = "/chat"
    ENDPOINT_QUERY = "/query"
    
    API_TIMEOUT = 30  
    # VECTOR_SEARCH_K = 4              # 기존값 (주석 보존)
    VECTOR_SEARCH_K = 10               # [추가 정의] 768차원 대응 상향

    # LangGraph 워크플로우 제어
    MAX_RETRIES = 3
    K_FAST = 4
    K_DEEP = 12

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
    print(f"📂 DB_PATH: {Settings.CHROMA_DB_PATH}")
    print(f"📂 COLLECTION: {Settings.CHROMA_COLLECTION_NAME}")
    print(f"📂 EMBEDDING: {Settings.EMBEDDING_MODEL} ({Settings.EMBEDDING_DIMENSION} dim)")
    print("="*80)
    print("✅ v5 설정 준비 완료: 월요일 768차원 벤치마크 가동 가능")
