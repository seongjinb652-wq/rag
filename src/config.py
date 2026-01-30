#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Day 1: 중앙 설정 관리 (v4 이어넣기 및 인식률 95% 최적화 버전)
v5 업데이트: 768차원 로컬 임베딩 및 2000자 청크 전략 추가 (기존 설정 보존)
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
    # [수정] DB 처리 모드: True면 초기화(v3), False면 이어넣기(v4)
    # ========================
    # RESET_DB = False  # 기존 v4 이어넣기 설정 (주석 보존)
    RESET_DB = True     # [추가 정의] v3 초기화: 차원 변경 시 필수 실행

    # ========================
    # [수정] 문서 처리 설정 (2000/200 튜닝 버전 추가)
    # ========================
    # CHUNK_SIZE = 1000       # 기존 1000자 설정 (주석 보존)
    # CHUNK_OVERLAP = 150     # 기존 150자 설정 (주석 보존)
    CHUNK_SIZE = 2000         # [추가 정의] 맥락 보존을 위한 확장
    CHUNK_OVERLAP = 200       # [추가 정의] 오버랩 확장
    
    SUPPORTED_FORMATS = {'.pdf', '.pptx', '.docx', '.txt', '.png', '.jpg', '.jpeg'}
    SLEEP_INTERVAL = 0.1  # 원하는 대기 시간 설정

    # ========================
    # [수정] 임베딩 설정 (768차원 로컬 모델 추가)

    # ========================
    # 벡터 DB 및 메타데이터 설정
    # ========================
    CHROMA_DB_PATH = _DATA_DIR / 'chroma_db'
    
    # [수정 불가/주석 보존] 기존 컬렉션명
    # CHROMA_COLLECTION_NAME = 'indonesia_pdt_docs' 
    
    # [추가 정의] v5 벤치마크용 컬렉션명
    # 모델명(bge)과 차원(768), 청크사이즈(2k)를 명시하면 관리가 훨씬 쉽습니다.
    CHROMA_COLLECTION_NAME = 'as_bge_768_c2000'
    # CHROMA_COLLECTION_NAME = 'indonesia_pdt_docs' 
    META_SOURCE_KEY = "source" 
    
    # ========================
    # [추가 정의] 필수 메타데이터 키 (2026-01-30 요청 반영)
    # ========================
    META_YEAR_KEY = "year"
    META_PROJECT_NAME = "project_name"
    META_DOC_TYPE = "doc_type" # 계약서/보고서/기획서
    
    # [신규 추가] 분석 고도화를 위한 확장 메타데이터
    # 벤치마크 시 검색 정밀도를 높이기 위해 추가를 추천합니다.
    META_INDUSTRY_KEY = "industry"   # 산업군 (예: 의료, 에너지, 건설) 
    # 추천 카테고리:     # medical(의료), energy(에너지), infra(인프라/건설), 
                        # gov(정부/행정), edu(교육), finance(금융)
    META_AUTHOR_KEY = "author"       # 작성자 또는 담당 부서
    
    # v4 이어넣기 상태 파일 (DATA_DIR 내부 고정)
    BATCH_STATE_FILE = _DATA_DIR / 'batch_state_local.json'
    # ========================
    # [추가 정의] Step 1~4 워크플로우 연동 메타데이터
    # ========================
    META_TOC_KEY = "toc_title"     # Step 1~2: 목차 생성 및 검증용 (전체 구조)
    META_SECTION_KEY = "section"   # Step 3~4: 섹션별 상세 생성 및 검증용 (상세 내용)
    
    # 앵커 정의 (문서 내 절대 좌표)
    # 계약서면 'Article', 보고서면 'Page', 기획서면 'Slide'가 이 값에 담깁니다.
    META_ANCHOR_KEY = "anchor"
    # [추가 정의] 앵커 세부 유형 (문서 종류에 따른 동적 할당용)
    META_PAGE_KEY = "page_label"  # PDF 실제 페이지 번호
    META_SECTION_KEY = "section"  # 계약서 조항(Clause) 또는 목차명
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
    # VECTOR_SEARCH_K = 5   # 기존값 (주석 보존)
    # VECTOR_SEARCH_K = 4   # 기존값 (주석 보존)
    VECTOR_SEARCH_K = 10    # [추가 정의] 768차원 및 대용량 청크 대응을 위한 상향

    # ========================
    # [추가 정의] LangGraph 워크플로우 제어값
    # ========================
    MAX_RETRIES = 3
    K_FAST = 4
    K_DEEP = 12

    @classmethod
    def validate(cls):
        """필수 설정 검증"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("필수 설정 누락: OPENAI_API_KEY")
        return True

    # ========================
    # 음성지원 설정
    # ========================

# 폴더 초기화 실행
Settings.init_directories()

if __name__ == "__main__":
    print("="*80)
    print(f"📂 PROJECT_ROOT: {PROJECT_ROOT}")
    print(f"📂 DATA_DIR: {Settings.DATA_DIR}")
    print(f"📂 DB_PATH: {Settings.CHROMA_DB_PATH}")
    print(f"📂 STATE_FILE: {Settings.BATCH_STATE_FILE}")
    print(f"📂 EMBEDDING: {Settings.EMBEDDING_MODEL} ({Settings.EMBEDDING_DIMENSION} dim)")
    print("="*80)
    print("✅ 설정 및 디렉토리 준비 완료 (v5 768차원 모드)")
