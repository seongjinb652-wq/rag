#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Streamlit 웹 UI - RAG 챗봇
목표: 사용자 인터페이스로 RAG 엔진 제어
소유자 : 성진
날자   : 2026-01-26

기능:
- 실시간 질문 입력
- 검색 결과 표시
- 답변 생성 및 표시
- 대화 히스토리
- 검색 결과 시각화

실행: streamlit run app_chatbot.py
"""

import streamlit as st
from pathlib import Path
import sys
import json
from datetime import datetime

# path 설정.
# config.py 로드
PROJECT_ROOT = Path(__file__).parent.parent
config_file = PROJECT_ROOT / 'config.py'

import importlib.util
spec = importlib.util.spec_from_file_location("config", config_file)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

Settings = config_module.Settings

# RAG 엔진 임포트
# sys.path.insert(0, str(PROJECT_ROOT / 'src' / 'rag'))
sys.path.insert(0, str(PROJECT_ROOT / 'rag'))
from setup_rag_engine import RAGEngine

# ========================
# Streamlit 설정
# ========================

st.set_page_config(
    page_title="RAG 챗봇",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 커스터마이징
st.markdown("""
<style>
    .main {
        padding: 0rem 0rem;
    }
    .stChatMessage {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ========================
# 세션 상태 초기화
# ========================

@st.cache_resource
def init_rag_engine():
    """RAG 엔진 초기화 (캐시)"""
    import chromadb
    # chromadb.config.settings.telemetry = False # ChromaDB 0.3.x ~ 0.4.x 초반 방식
    # return RAGEngine()                         # ChromaDB 0.3.x ~ 0.4.x 초반 방식
    from chromadb.config import Settings
    client_settings = Settings(anonymized_telemetry=False) # telemetry 끄기.  ChromaDB 0.5.x (현재) 방식
    
    return RAGEngine(settings=client_settings)  # RAGEngine 초기화 시 client_settings 전달. ChromaDB 0.5.x (현재) 방식


def init_session_state():
    """세션 상태 초기화"""
    if 'rag_engine' not in st.session_state:
        st.session_state.rag_engine = init_rag_engine()
    
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []


# ========================
# UI 함수
# ========================

def render_header():
    """헤더 렌더링"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.image("https://raw.githubusercontent.com/streamlit/streamlit/develop/docs/static/img/streamlit_logo.png", 
                width=50)
    
    with col2:
        st.title("🤖 RAG 챗봇")
        st.markdown("**문서 기반 질문 답변 시스템**")
    
    with col3:
        st.metric(
            label="검색 문서",
            value=st.session_state.rag_engine.collection.count(),
            delta="개"
        )


def render_sidebar():
    """사이드바 렌더링"""
    with st.sidebar:
        st.header("⚙️ 설정")
        
        st.subheader("검색 설정")
        search_k = st.slider(
            "검색 결과 수",
            min_value=1,
            max_value=10,
            value=Settings.VECTOR_SEARCH_K,
            help="유사 문서 검색 개수"
        )
        
        st.subheader("모델 정보")
        st.text_input(
            "LLM 모델",
            value=Settings.ANTHROPIC_MODEL,
            disabled=True
        )
        
        st.text_input(
            "임베딩 모델",
            value=Settings.EMBEDDING_MODEL.split('/')[-1],
            disabled=True
        )
        
        st.subheader("문서 정보")
        db_stats = st.session_state.rag_engine.get_stats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("저장 문서", db_stats['total_documents'])
        with col2:
            st.metric("임베딩 차원", db_stats['embedding_dimension'])
        
        st.divider()
        
        st.subheader("대화 관리")
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.session_state.search_results = []
            st.success("대화가 초기화되었습니다!")
        
        if st.button("💾 대화 저장", use_container_width=True):
            save_conversation()
        
        return search_k


def render_chat_history():
    """대화 히스토리 렌더링"""
    st.subheader("💬 대화 히스토리")
    
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])


def render_search_results(results):
    """검색 결과 렌더링"""
    if not results:
        st.info("검색 결과가 없습니다.")
        return
    
    st.subheader(f"📚 검색 결과 ({len(results)}개)")
    
    for i, doc in enumerate(results, 1):
        with st.expander(
            f"📄 결과 {i} - 유사도: {doc['similarity']}",
            expanded=(i == 1)
        ):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown("**내용:**")
                st.markdown(doc['text'][:300] + "..." if len(doc['text']) > 300 else doc['text'])
            
            with col2:
                st.markdown("**메타데이터:**")
                st.markdown(f"**출처:** {doc['source']}")
                st.markdown(f"**유사도:** {doc['similarity']}")


def process_query(query: str, search_k: int):
    """쿼리 처리"""
    if not query.strip():
        st.warning("질문을 입력해주세요!")
        return
    
    # 로딩 상태 표시
    with st.spinner("🔍 검색 중..."):
        # RAG 파이프라인 실행
        result = st.session_state.rag_engine.query(
            question=query,
            verbose=False
        )
    
    # 검색 결과 저장
    st.session_state.search_results = result['documents']
    
    # 대화 히스토리에 추가
    st.session_state.messages.append({
        'role': 'user',
        'content': query,
        'timestamp': datetime.now().isoformat()
    })
    
    st.session_state.messages.append({
        'role': 'assistant',
        'content': result['answer'],
        'timestamp': datetime.now().isoformat(),
        'elapsed_time': result['elapsed_time']
    })


def save_conversation():
    """대화 저장"""
    if not st.session_state.messages:
        st.warning("저장할 대화가 없습니다!")
        return
    
    save_path = Settings.LOGS_DIR / f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(st.session_state.messages, f, ensure_ascii=False, indent=2)
    
    st.success(f"대화가 저장되었습니다: {save_path}")


# ========================
# 메인 UI
# ========================

def main():
    """메인 함수"""
    
    # 세션 상태 초기화
    init_session_state()
    
    # 헤더
    render_header()
    
    st.divider()
    
    # 레이아웃
    col_chat, col_sidebar = st.columns([3, 1])
    
    # 사이드바
    with col_sidebar:
    #    search_k = render_sidebar()
        search_k = st.slider(
            "검색 결과 수",
            min_value=1,
            max_value=10,
            value=Settings.VECTOR_SEARCH_K,
            help="유사 문서 검색 개수"
        )

    
    # 메인 채팅 영역
    with col_chat:
        # 대화 히스토리
        st.subheader("💬 대화")
        render_chat_history()
        
        st.divider()
        
        # 질문 입력
        st.subheader("🎯 질문 입력")
        query = st.text_area(
            "질문을 입력하세요:",
            placeholder="예: 서울에 대해 알려줘",
            height=100,
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("🚀 질문하기", use_container_width=True):
                process_query(query, search_k)
        
        with col2:
            if st.button("🎲 예시", use_container_width=True):
                st.session_state.example_query = "서울에 대해 알려줘"
        
        st.divider()
        
        # 검색 결과
        if st.session_state.search_results:
            render_search_results(st.session_state.search_results)


if __name__ == "__main__":
    main()
