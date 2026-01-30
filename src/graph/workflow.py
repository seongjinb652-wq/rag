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
# def planner(state: GraphState):
#    print("---[STEP 1] PLANNER: 분석 및 작업 설계---")
#    # TODO: 질문의 복잡도를 판단하여 단계를 나누는 로직 (config_graph의 기준 사용 예정)
#    return {"status_msg": "작업 계획 수립 완료"}
def planner(state: GraphState):
    print("---[STEP 1] PLANNER: 보고서 목차 생성---")
    question = state.get("question", "")
    
    # [사용자님 핵심 로직]: CONFIG의 TOC_TEMPLATES를 참고하여 목차 생성
    planner_prompt = f"""
    당신은 아티스트썸의 수석 전략가입니다.
    질문: {question}
    표준 템플릿: {CONFIG.get('TOC_TEMPLATES', {})}
    
    위 질문에 답변하기 위해 가장 적합한 보고서 목차를 리스트 형식으로 만드세요.
    반드시 데이터에 근거해 작성할 수 있는 실무적인 목차여야 합니다.
    형식 예시: ["목차1", "목차2", "목차3"]
    """
    
    response = llm.invoke(planner_prompt).content
    # 문자열 형태의 리스트를 실제 파이썬 리스트로 변환 (간단한 파싱)
    try:
        import json
        plan = json.loads(response.replace("'", '"'))
    except:
        plan = [p.strip() for p in response.replace("[", "").replace("]", "").split(",")]

    return {"plan": plan, "status_msg": "목차 생성 완료"}
# 2. 플래너 채점 (Plan Check)
# def check_plan(state: GraphState):
#    print("---[STEP 2] PLAN CHECK: 설계 적합성 검토---")
#    return state
def planner_grader(state: GraphState):
    print("---[STEP 2] PLANNER GRADER: 목차 적합성 검증---")
    
    question = state.get("question", "")
    plan = state.get("plan", [])
    
    grading_prompt = f"""
    당신은 품질 관리자입니다. 
    사용자 질문: {question}
    생성된 목차: {plan}
    
    이 목차들이 사용자의 질문에 답하기에 충분하고 논리적인 구조입니까?
    - 점수: 0~100점
    - 기준: 80점 이상이면 'Yes', 미만이면 'No'
    
    결과 형식: 점수 | 판정(Yes/No) | 이유
    """
    
    response = llm.invoke(grading_prompt).content.lower()
    
    if "yes" in response:
        print("---[CHECK] 목차 승인: 3단계로 이동합니다.---")
        return {"is_relevant": "yes"}
    else:
        print("---[CHECK] 목차 반려: 재설계가 필요합니다.---")
        return {"is_relevant": "no"}
        
# 3. 각 단계 실행 (Execute)
# def execute_step(state: GraphState):
#     print("---[STEP 3] EXECUTE: 데이터 검색 및 가공---")
#     # TODO: config_graph에서 정의한 K값 적용 예정
#     return {"documents": ["연도별 프로젝트 데이터 샘플"]}

# [STEP 3-A] Search: 기본 골격 복구 (상세화 전 기본 검색)
# def search_node(state: GraphState):
#     print(f"---[STEP 3-A] SEARCH: 기본 데이터 수집 (Retry: {state.get('current_retry', 0)})---")
#     question = state.get("question", "")
#     current_retry = state.get("current_retry", 0)
    
#     # [기본 골격]: 질문 복잡도에 따라 K값 결정
#     k = CONFIG["K_DEEP"] if current_retry > 0 or any(kw in question for kw in CONFIG["COMPLEX_KEYWORDS"]) else CONFIG["K_FAST"]
    
#     # retriever는 외부 정의된 것으로 가정
#     docs = retriever.invoke(question, k=k) 
#     return {"documents": docs, "current_retry": current_retry}

# # [STEP 3-B] Stepwise Generator: 목차별 상세 생성 (중요한 것만 기술)
# def stepwise_generator(state: GraphState):
#     print("---[STEP 3-B] GENERATOR: 목차별 상세 작성---")
#     docs = state.get("documents", [])
#     plan = state.get("plan", [])
    
#     context = "\n".join(docs)
#     hint = CONFIG.get("SUMMARIZATION_HINT", "")
    
#     generated_sections = []
#     for section in plan:
#         prompt = f"데이터: {context}\n항목: {section}\n지침: {hint}\n전문적으로 작성하라."
#         response = llm.invoke(prompt).content
#         generated_sections.append(f"### {section}\n{response}")
    
#     return {"generation": "\n\n".join(generated_sections)}




def search_node(state: GraphState):
    question = state.get("question", "")
    current_retry = state.get("current_retry", 0)
    
    # . 시도 횟수에 따른 K값 결정
    k = CONFIG["K_DEEP"] if current_retry > 0 or any(kw in question for kw in CONFIG["COMPLEX_KEYWORDS"]) else CONFIG["K_FAST"]
    
    print(f"---[STEP 3] SEARCH: 시도 {current_retry + 1}회 (K={k})---")
    
    # . 검색 실행 (VectorDB 등에서 조회)
    new_docs = retriever.invoke(question, k=k) # 예시 함수
    
    # . 평가 (검색 결과가 충분한지 LLM이 판단)
    # [사용자님 로직]: "데이터가 0개거나 질문에 답하기 부족하면 재시도"
    if not new_docs and current_retry < CONFIG["MAX_RETRIES"]:
        print("---[RETRY] 결과 부족, 다시 시도합니다.---")
        return {"documents": new_docs, "current_retry": current_retry + 1, "is_relevant": "retry"}
    
    return {"documents": new_docs, "is_relevant": "yes", "status_msg": "검색 완료"}

# [STEP 3] 목차별 답변 생성 (데이터 선별 기술 로직 포함)

def stepwise_generator(state: GraphState):
    print("---[STEP 3] GENERATOR: 목차별 상세 생성 (3회 반복 루프 포함)---")
    
    docs = state.get("documents", [])
    plan = state.get("plan", [])
    question = state.get("question", "")
    current_retry = state.get("current_retry", 0)
    
    # [사용자님 핵심 로직 1]: 데이터가 많을 경우 중요한 것만 기술
    context = "\n".join(docs)
    summarization_hint = CONFIG.get("SUMMARIZATION_HINT", "데이터가 많으면 규모가 크고 대표적인 것 위주로 기술하고 나머지는 '이외 다수'로 표기.")
    
    generated_sections = []
    
    # [사용자님 핵심 로직 2]: 목차(plan)별로 순회하며 답변 생성
    for section in plan:
        print(f"---[{section}] 항목 생성 중...---")
        prompt = f"""
        당신은 아티스트썸의 전략 분석가입니다. 
        질문: {question}
        항목: {section}
        데이터: {context}
        
        지침:
        1. 반드시 제공된 데이터에 근거하여 '{section}' 내용을 작성하세요.
        2. {summarization_hint}
        3. 비즈니스 톤을 유지하며 구체적인 수치나 프로젝트명이 있다면 포함하세요.
        """
        
        section_response = llm.invoke(prompt).content
        generated_sections.append(f"### {section}\n{section_response}")
    
    full_generation = "\n\n".join(generated_sections)
    
    # [사용자님 핵심 로직 3]: 3회 반복(Retry) 제어용 상태 업데이트
    # (여기서 생성된 결과가 부실하면 4단계 채점에서 retry를 보낼 것입니다)
    return {
        "generation": full_generation,
        "current_retry": current_retry, 
        "status_msg": f"목차별 생성 완료 (현재 시도: {current_retry + 1}/3)"
    }
    
# 4. 각 단계 채점 (Step Check/Grader)
# def check_step(state: GraphState):
#    print("---[STEP 4] STEP CHECK: 데이터 관련성 및 누락 검수---")
#    # 사용자님이 작성하신 Grader 로직의 핵심
#    # response = llm.invoke(grader_prompt) 
#    return {"is_relevant": "yes"} # 혹은 "no"
# [STEP 4] 목차별 데이터 충족도 채점
def step_grader(state: GraphState):
    print("---[STEP 4] GRADER: 목차별 단계별 채점 실시---")
    
    docs = state.get("documents", [])
    plan = state.get("plan", [])
    
    scored_results = {}
    insufficient_plans = []

    # [사용자님 핵심 로직]: 목차별로 데이터가 충분한지 LLM이 채점
    for step in plan:
        print(f"---[{step}] 항목 채점 중...---")
        grading_prompt = f"""
        당신은 데이터 감사관입니다.
        [목차 항목]: {step}
        [검색된 데이터]: {docs}
        
        지침:
        위 데이터를 바탕으로 '{step}' 내용을 작성하기에 충분한 정보가 있습니까?
        점수는 0~100점으로 매기고, 70점 미만이면 'No', 이상이면 'Yes'로 답하세요.
        
        형식: 점수 | 판정(Yes/No) | 이유
        """
        
        response = llm.invoke(grading_prompt).content
        # 예: "85 | Yes | 프로젝트 연도와 예산 내역이 포함됨"
        
        if "no" in response.lower():
            insufficient_plans.append(step)
        
        scored_results[step] = response

    # 과반수 이상의 항목이 부실하거나 핵심 항목이 빠졌을 때 재시도 결정
    if insufficient_plans and state.get("current_retry", 0) < CONFIG["MAX_RETRIES"]:
        print(f"---[ALERT] 부족한 항목 발견: {insufficient_plans}---")
        return {
            "is_relevant": "retry", 
            "status_msg": f"부족 항목 보강 필요: {insufficient_plans}",
            "current_retry": state.get("current_retry", 0) + 1
        }

    return {
        "is_relevant": "yes", 
        "status_msg": "모든 단계 채점 완료 (또는 최대 재시도 도달)"
    }


# 5. 최종 채점 (Final Check)
# def final_check(state: GraphState):
#     print("---[STEP 5] FINAL CHECK: 최종 결과 완결성 검증---")
#     return state
# [STEP 5] 할루시네이션 및 답변 적절성 검증
def hallucination_grader(state: GraphState):
    print("---[STEP 5] GRADER: 생성 결과 검증---")
    
    generation = state.get("generation", "")
    docs = state.get("documents", [])
    question = state.get("question", "")
    current_retry = state.get("current_retry", 0)

    # . 근거 확인 프롬프트 (Grounding Check)
    grade_prompt = f"""
    당신은 엄격한 팩트체커입니다.
    [데이터]: {docs}
    [생성된 답변]: {generation}
    
    지침:
    1. 답변이 제공된 데이터에만 기반하고 있습니까? (Yes/No)
    2. 데이터에 없는 내용을 지어내지는 않았습니까?
    
    결과는 반드시 'yes' 또는 'no'로만 대답하세요.
    """
    
    # LLM을 통한 판정
    grade = llm.invoke(grade_prompt).content.strip().lower()
    
    if "yes" in grade:
        print("---[CHECK] 통과: 근거가 확실합니다.---")
        return {"is_relevant": "yes", "status_msg": "검증 완료 - 다음 단계로 이동"}
    else:
        # [사용자님 로직]: 검증 실패 시 재시도 횟수 확인 후 다시 검색으로 보냄
        if current_retry < CONFIG["MAX_RETRIES"]:
            print(f"---[CHECK] 실패: 할루시네이션 발견! 재시도합니다. ({current_retry + 1})---")
            return {"is_relevant": "no", "current_retry": current_retry + 1, "status_msg": "재검색 요청"}
        else:
            print("---[CHECK] 실패: 최대 재시도 도달. 최선을 다해 취합합니다.---")
            return {"is_relevant": "yes", "status_msg": "최대 시도 도달 - 강제 통과"}
            
# 6. 결과 도출 (Final Answer)
# def responder(state: GraphState):
#    print("---[STEP 6] RESPONDER: 최종 답변 및 문서 출력---")
#    return {"generation": "요청하신 연도별 정리 작업이 완료되었습니다."}
def generator(state: GraphState):
    print("---[STEP 6] GENERATOR: 심층 분석 및 취합---")
    docs = state.get("documents", [])
    plan = state.get("plan", []) # Planner가 생성한 목차 리스트
    
    final_sections = []
    
    # [사용자님 핵심 로직]: 목차별로 루프를 돌며 상세 작성
    for section in plan:
        print(f"---[{section}] 작성 중...---")
        section_prompt = f"""
        당신은 전략 컨설턴트입니다. 다음 데이터를 바탕으로 보고서의 '{section}' 파트를 작성하세요.
        - 데이터: {docs}
        - 지침: {CONFIG['SUMMARIZATION_HINT']}
        """
        section_content = llm.invoke(section_prompt).content
        final_sections.append(f"## {section}\n{section_content}")
    
    full_report = "\n\n".join(final_sections)
    
    # 파일 저장 (PDF/Word를 염두에 둔 텍스트 저장)
    with open("ArtistSum_Final_Report.txt", "w", encoding="utf-8") as f:
        f.write(full_report)
        
    return {"generation": full_report}
    
# def generator(state: GraphState):
#     print("---[STEP 6] GENERATOR: 최종 분석 및 문서 생성---")
    
#     docs = state.get("documents", [])
#     question = state.get("question", "")
#     plan = state.get("plan", [])
    
#     # 1. 컨텍스트 구성 (데이터 과다 시 요약 지침 반영)
#     context = "\n".join(docs)
#     hint = CONFIG.get("SUMMARIZATION_HINT", "")
    
#     # 2. 페르소나 및 프롬프트 설정
#     system_prompt = f"""
#     당신은 아티스트썸의 전략 기획 실장입니다. 
#     제공된 {len(docs)}개의 프로젝트 데이터를 바탕으로 '{question}'에 대한 최종 답변을 작성하세요.
    
#     [지침]
#     - 목차 구조: {plan}
#     - 요약 가이드: {hint}
#     - 전문적이고 신뢰감 있는 비즈니스 톤을 유지할 것.
#     """
    
#     # 3. 답변 생성
#     response = llm.invoke([
#         ("system", system_prompt),
#         ("user", f"데이터: {context}\n\n위 데이터를 바탕으로 정교한 보고서를 작성해줘.")
#     ])
    
#     final_report = response.content
    
#     # 4. 실제 파일(Word/PDF 대용 텍스트) 생성 로직
#     # 사용자님이 원하셨던 '투자제안서', '리스트업' 등의 파일 저장 기능
#     file_name = f"ArtistSum_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
#     with open(file_name, "w", encoding="utf-8") as f:
#         f.write(f"제목: {question}\n")
#         f.write("-" * 50 + "\n")
#         f.write(final_report)
    
#     print(f"---[INFO] 보고서 파일 생성 완료: {file_name}---")

#     return {
#         "generation": final_report,
#         "status_msg": "최종 보고서 및 파일 생성 완료"
#     }
# --- [Conditional Logic: 분기 판단] ---

def decide_next_path(state: GraphState):
    # 4단계 채점 결과가 'no'이거나 문서가 비어있으면 재실행(또는 종료)
    if state.get("is_relevant") == "no" or not state.get("documents"):
        print("---[RETRY] 데이터 부족 또는 부적합! 다시 실행합니다.---")
        return "retry"
    return "success"

# --- [Graph Build: 노드 연결] ---
# [Graph 정의]
from langgraph.graph import StateGraph, END

workflow = StateGraph(GraphState)

# 노드 추가
workflow.add_node("planner", planner)
workflow.add_node("search", search_node) # 3단계 (K_DEEP 적용 지점)
workflow.add_node("generator", generator)

# 엣지 연결 (사용자님의 '이를 바탕으로' 로직 반영)
workflow.set_entry_point("planner")
workflow.add_edge("planner", "search")
workflow.add_edge("search", "generator")
workflow.add_edge("generator", END)

app = workflow.compile()



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




