# workflow.py 내 grade_documents 함수 예시
def grade_documents(state: GraphState):
    question = state["question"]
    docs = state["documents"]
    
    # LLM에게 채점 요청 (프롬프트가 핵심!)
    # 관련 있으면 "yes", 없으면 "no"를 반환하도록 설계
    # 결과가 "no"라면 state["documents"]를 비우거나 필터링합니다.
    return {"documents": filtered_docs, "is_relevant": "no_if_empty"}

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
