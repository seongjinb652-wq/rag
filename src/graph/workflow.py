# workflow.py 내 grade_documents 함수 예시
# 1. 프롬프트 정의
instruction = """너는 전문 검수관이다. 
검색된 문서가 사용자의 질문과 관련이 있는지 엄격하게 채점하라.
질문에 답하기에 정보가 부족하거나, 주제가 80% 이상 일치하지 않는다면 가차 없이 'no'라고 판정하라.
다른 설명 없이 오직 'yes' 또는 'no'로만 대답해야 한다."""

# 2. 실제 노드 함수 내 적용 예시
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

