import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA

# .env 로드
load_dotenv()

# 설정
DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
COLLECTION_NAME = "indonesia_pdt_docs"

def test_rag_query(query):
    # 1. 임베딩 및 DB 연결
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_db = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )

    # 2. 모델 설정 (답변용 GPT-4o)
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

    # 3. RAG 체인 구축
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k": 5}), # 관련 문서 5개 참조
        return_source_documents=True
    )

    # 4. 질문 실행
    print(f"\n🙋 질문: {query}")
    print("-" * 50)
    result = qa_chain.invoke({"query": query})

    print(f"🤖 답변:\n{result['result']}")
    print("-" * 50)
    
    # 참조된 소스 파일 확인
    print("📚 참고한 문서 목록:")
    sources = set([doc.metadata['source'] for doc in result['source_documents']])
    for src in sources:
        print(f"- {src}")

if __name__ == "__main__":
    # 테스트 질문
    user_query = "인도네시아 PDT 사업의 리스크가 뭐야? 사업성 평가 보고서 내용을 중심으로 알려줘."
    test_rag_query(user_query)
