import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# .env 로드
load_dotenv()

# 설정
DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
COLLECTION_NAME = "indonesia_pdt_docs"

def test_rag_query(query):
    # 1. 임베딩 설정 (v4 적재 시 사용한 모델)
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

        # 4. 프롬프트 템플릿 설정 (시스템 역할 부여)
        system_prompt = (
            "당신은 문서 검색 보조원입니다. "
            "아래 제공된 문맥(context)만을 사용하여 질문에 답하세요. "
            "답을 모르면 모른다고 하되, 추측하지 마세요. "
            "한국어로 답변하세요."
            "\n\n"
            "{context}"
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        # 5. RAG 체인 구축 (최신 create_retrieval_chain 방식)
        combine_docs_chain = create_stuff_documents_chain(llm, prompt)
        retrieval_chain = create_retrieval_chain(vector_db.as_retriever(search_kwargs={"k": 5}), combine_docs_chain)

        # 6. 질문 실행
        print(f"\n🙋 질문: {query}")
        print("-" * 50)
        
        # 최신 invoke 방식 사용
        response = retrieval_chain.invoke({"input": query})

        print(f"🤖 답변:\n{response['answer']}")
        print("-" * 50)
        
        # 참조된 소스 확인
        print("📚 참고한 문서 목록:")
        sources = set([doc.metadata['source'] for doc in response['context']])
        for src in sources:
            print(f"- {src}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    user_query = "인도네시아 PDT 사업의 리스크가 뭐야? 사업성 평가 보고서 내용을 중심으로 알려줘."
    test_rag_query(user_query)
