import os
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from config import Settings # 중앙 설정 참조

def search_test():
    # 1. DB 및 모델 설정 (기존 값 주석 보존)
    # DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
    db_path = str(Settings.CHROMA_DB_PATH)
    # COLLECTION_NAME = "indonesia_pdt_docs"
    collection_name = Settings.CHROMA_COLLECTION_NAME
    # embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    embeddings = OpenAIEmbeddings(model=Settings.EMBEDDING_MODEL)

    # 2. 벡터 DB 연결
    vector_db = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings,
        collection_name=collection_name
    )

    # 3. 검색 및 LLM 설정 (기존 값 주석 보존)
    # llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    llm = ChatOpenAI(model_name=Settings.OPENAI_MODEL, temperature=0)
    
    query = "인도네시아 PDT 암센터 건립 예산은 얼마인가요?" 
    print(f"\n🔍 질문: {query}")

    # 4. 유사도 검색 실행 (K값 Settings 연동)
    # docs = vector_db.similarity_search(query, k=5)
    docs = vector_db.similarity_search(query, k=Settings.VECTOR_SEARCH_K)

    print(f"\n📄 검색된 문서 개수: {len(docs)}")
    print("-" * 50)

    for i, doc in enumerate(docs, 1):
        # [지시사항] META_SOURCE_KEY를 활용한 출처 출력
        # source = doc.metadata.get("source", "알 수 없음")
        source = doc.metadata.get(Settings.META_SOURCE_KEY, "알 수 없음")
        
        print(f"[{i}] 출처: {os.path.basename(source)}")
        print(f"내용: {doc.page_content[:150]}...")
        print("-" * 50)

    # 5. LLM 답변 생성 테스트
    context = "\n\n".join([d.page_content for d in docs])
    prompt = f"다음 문맥을 바탕으로 질문에 답하세요:\n\n{context}\n\n질문: {query}"
    
    response = llm.invoke(prompt)
    print(f"\n🤖 LLM 답변:\n{response.content}")

if __name__ == "__main__":
    search_test()
