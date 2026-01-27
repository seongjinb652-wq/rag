#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import chromadb
from openai import OpenAI
from pathlib import Path

# 설정
DB_PATH = Path(r"C:/Users/USER/rag/src/data/chroma_db")
COLLECTION_NAME = "indonesia_pdt_docs"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = "text-embedding-3-small"

class RAGSearcher:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.db_client = chromadb.PersistentClient(path=str(DB_PATH))
        self.collection = self.db_client.get_collection(name=COLLECTION_NAME)

    def search(self, query_text: str, n_results: int = 3):
        # 1. 사용자의 질문을 벡터로 변환 (DB 저장할 때와 같은 모델 사용)
        response = self.client.embeddings.create(input=[query_text], model=EMBED_MODEL)
        query_embedding = response.data[0].embedding

        # 2. 유사도 검색
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        print(f"\n🙋 질문: {query_text}")
        print("-" * 50)

        # 3. 결과 출력
        for i in range(len(results['ids'][0])):
            distance = results['distances'][0][i]
            # Cosine 거리를 유사도 점수(0~1)로 변환
            score = 1 - distance 
            source = results['metadatas'][0][i]['source']
            content = results['documents'][0][i].replace('\n', ' ')

            print(f"[{i+1}] 유사도: {score:.4f} | 출처: {source}")
            print(f"📄 내용: {content[:150]}...")
            print("-" * 50)


if __name__ == "__main__":
    searcher = RAGSearcher()
    
    # 테스트할 질문 리스트
    test_queries = [
        "인도네시아 투자 박람회에서 소개된 PDT 치료의 특징은 뭐야?",
        "한경 부스 구매 의향 공문에 어떤 내용이 담겨 있어?"
    ]
    
    for i, user_query in enumerate(test_queries, 1):
        print(f"\n\n🚀 [테스트 질문 {i}] {user_query}")
        print("="*60)
        searcher.search(user_query)
        print("="*60)
