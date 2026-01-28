import os
from dotenv import load_dotenv
# 최신 임포트 경로 적용
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.chains import RetrievalQA

# .env 로드
load_dotenv()

# 설정
DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
COLLECTION_NAME = "indonesia_pdt_docs"

def test_rag_query(query):
    # 1. 임베딩 설정 (어제 v4 적재 때 사용한 모델과 반드시 동일해야 함)
    # 만약 계속 1536 vs 384 오류가 난다면, DB가 섞인 것이니 v3(초기화)를 한 번 하셔야 합니다.
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    try:
        # 2. DB 연결
        vector_db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )

        # 3. 모델 설정 (GPT-4o)
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

        # 4. RAG 체인 구축
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_db.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True
        )

        # 5. 질문 실행
        print(f"\n🙋 질문: {query}")
        print("-" * 50)
        result = qa_chain.invoke({"query": query})

        print(f"🤖 답변:\n{result['result']}")
        print("-" * 50)
        
        print("📚 참고한 문서 목록:")
        sources = set([doc.metadata['source'] for doc in result['source_documents']])
        for src in sources:
            print(f"- {src}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        if "dimension" in str(e):
            print("\n💡 팁: 임베딩 차원이 맞지 않습니다. DB를 삭제(v3 초기화)하고 다시 적재하거나, 이전에 썼던 임베딩 모델로 바꿔야 합니다.")

if __name__ == "__main__":
    user_query = "인도네시아 PDT 사업의 리스크가 뭐야? 사업성 평가 보고서 내용을 중심으로 알려줘."
    test_rag_query(user_query)
