import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# .env 로드
load_dotenv()

# 경로 설정
DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
COLLECTION_NAME = "indonesia_pdt_docs"

def test_stable_rag(query):
    # 1. 임베딩 (어제 적재한 모델 그대로 사용)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    try:
        # 2. DB 연결 (안정된 community 버전의 Chroma 사용)
        vector_db = Chroma(
            persist_directory=DB_PATH,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )

        # 3. 모델 설정 (GPT-4o)
        llm = ChatOpenAI(model_name="gpt-4o", temperature=0)

        # 4. RetrievalQA 체인 (가장 직관적이고 ASR 연결 시 가공하기 편함)
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vector_db.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True
        )

        print(f"\n🙋 질문: {query}")
        print("-" * 50)
        
        result = qa.invoke({"query": query})

        print(f"🤖 답변:\n{result['result']}")
        print("-" * 50)
        
        # 소스 확인
        sources = set([doc.metadata['source'] for doc in result['source_documents']])
        print(f"📚 참고문헌: {', '.join(sources)}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    test_stable_rag("인도네시아 PDT 사업의 리스크가 뭐야? 사업성 평가 보고서 내용을 중심으로 알려줘.")
