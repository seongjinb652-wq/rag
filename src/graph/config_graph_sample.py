from typing import List, Optional, TypedDict
from langchain_openai import ChatOpenAI
# ==========================================================
# [Monitoring & Evaluation Option]
# ==========================================================
# LangSmith 사용 시 아래 설정 활성화 가능 (현재 비활성)
# USE_LANGSMITH = False 
# ※ 주의: LangSmith 사용 시 외부 API 호출로 인한 [비용 추가] 및 [Latency 발생] 우려.
# ※ 현재는 '80% 일치성'과 '속도' 확보를 위해 프롬프트 기반 [내부 채점] 로직 사용 중.
# ----------------------------------------------------------
# import os
# os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com" # 3. 평가 실행 대체.
# ==========================================================
USE_LANGSMITH = False 

# 1. 상태 정의 (데이터 바구니)
class GraphState(TypedDict):
    question: str
    status_msg: Optional[str]
    plan: Optional[List[str]]
    documents: List[str]
    is_relevant: str        # yes / no / retry
    generation: str
    current_retry: int      # 무한 루프 방지

# 2. 에이전트 행동 설정 (수치 관리)
CONFIG = {
    "K_FAST": 4,                # 일반 모드
    "K_DEEP": 20,               # 심층/취합 모드
    "MAX_RETRIES": 3,           # 최대 재시도 횟수
    "COMPLEXITY_KEYWORDS": ["연도별", "목록", "정리", "취합", "만들어줘"]
}

# 3. LLM 설정 (전역 사용)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

