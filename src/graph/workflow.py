# workflow.py 내 grade_documents 함수 예시
# 1. 프롬프트 정의
instruction = """너는 전문 검수관이다. 
검색된 문서가 사용자의 질문과 관련이 있는지 엄격하게 채점하라.
질문에 답하기에 정보가 부족하거나, 주제가 80% 이상 일치하지 않는다면 가차 없이 'no'라고 판정하라.
다른 설명 없이 오직 'yes' 또는 'no'로만 대답해야 한다."""
from langgraph.graph import END, StateGraph
from .config_graph import GraphState, llm

# --- [Nodes: 6단계 핵심 로직] ---

# 1. 플래너 구동 (Plan)
def planner(state: GraphState):
    print("---[STEP 1] PLANNER: 분석 및 작업 설계---")
    # TODO: 질문의 복잡도를 판단하여 단계를 나누는 로직 (config_graph의 기준 사용 예정)
    return {"status_msg": "작업 계획 수립 완료"}

# 2. 플래너 채점 (Plan Check)
def check_plan(state: GraphState):
    print("---[STEP 2] PLAN CHECK: 설계 적합성 검토---")
    return state

# 3. 각 단계 실행 (Execute)
def execute_step(state: GraphState):
    print("---[STEP 3] EXECUTE: 데이터 검색 및 가공---")
    # TODO: config_graph에서 정의한 K값 적용 예정
    return {"documents": ["연도별 프로젝트 데이터 샘플"]}

# 4. 각 단계 채점 (Step Check/Grader)
def check_step(state: GraphState):
    print("---[STEP 4] STEP CHECK: 데이터 관련성 및 누락 검수---")
    # 사용자님이 작성하신 Grader 로직의 핵심
    # response = llm.invoke(grader_prompt) 
    return {"is_relevant": "yes"} # 혹은 "no"

# 5. 최종 채점 (Final Check)
def final_check(state: GraphState):
    print("---[STEP 5] FINAL CHECK: 최종 결과 완결성 검증---")
    return state

# 6. 결과 도출 (Final Answer)
def responder(state: GraphState):
    print("---[STEP 6] RESPONDER: 최종 답변 및 문서 출력---")
    return {"generation": "요청하신 연도별 정리 작업이 완료되었습니다."}

# --- [Conditional Logic: 분기 판단] ---

def decide_next_path(state: GraphState):
    # 4단계 채점 결과가 'no'이거나 문서가 비어있으면 재실행(또는 종료)
    if state.get("is_relevant") == "no" or not state.get("documents"):
        print("---[RETRY] 데이터 부족 또는 부적합! 다시 실행합니다.---")
        return "retry"
    return "success"

# --- [Graph Build: 노드 연결] ---

workflow = StateGraph(GraphState)

workflow.add_node("planner", planner)
workflow.add_node("check_plan", check_plan)
workflow.add_node("execute_step", execute_step)
workflow.add_node("check_step", check_step)
workflow.add_node("final_check", final_check)
workflow.add_node("responder", responder)

# 연결 구성
workflow.set_entry_point("planner")
workflow.add_edge("planner", "check_plan")
workflow.add_edge("check_plan", "execute_step")
workflow.add_edge("execute_step", "check_step")

# 조건부 루프: 채점 결과에 따라 3번으로 돌아가거나 5번으로 전진
workflow.add_conditional_edges(
    "check_step",
    decide_next_path,
    {
        "retry": "execute_step",
        "success": "final_check"
    }
)

workflow.add_edge("final_check", "responder")
workflow.add_edge("responder", END)

app = workflow.compile()


# 실제 노드 함수 내 적용 예시
def grade_documents(state: GraphState):
    question = state["question"]
    documents = state["documents"]
    
    # 여기서 LLM을 호출할 때 사용할 템플릿
    prompt = f"""{instruction}
    
    회원 질문: {question}
    검색된 문서: {documents}
    
    결과(yes/no):"""
    
    # response = llm.invoke(prompt) # 실제 호출 시점
    print("---[CHECK] 검수 완료---")
    return {"is_relevant": "yes"} # 혹은 결과에 따라 'no'
    
    # LLM에게 채점 요청 (프롬프트가 핵심!)
    # 관련 있으면 "yes", 없으면 "no"를 반환하도록 설계
    # 결과가 "no"라면 state["documents"]를 비우거나 필터링합니다.

# workflow.py 하단
def decide_to_generate(state):
    if not state["documents"]: # 관련 문서가 하나도 없다면
        return "end"            # 여기서 종료 (또는 질문 재구성)
    return "generate"           # 답변 생성으로 진행

workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "end": END,
        "generate": "generate"
    }
)


