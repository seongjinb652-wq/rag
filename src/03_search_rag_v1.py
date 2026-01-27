def search(self, user_query: str, k: int = 5):
        # 1. 벡터 검색 수행
        query_embedding = self.get_embedding(user_query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k * 2 # 후보군을 넉넉히 뽑습니다
        )

        # 2. 하이브리드 점수 재계산 (키워드 가중치)
        # 쿼리에서 핵심 키워드 추출 (단순 공백 분리 혹은 중요 단어)
        keywords = [kw for kw in user_query.split() if len(kw) > 1]
        
        scored_results = []
        for i in range(len(results['documents'][0])):
            doc = results['documents'][0][i]
            metadata = results['metadatas'][0][i]
            dist = results['distances'][0][i]
            
            # 기본 점수 (거리 기반, 낮을수록 좋음 -> 높을수록 좋게 변환)
            score = 1 - dist
            
            # 키워드 보너스 (중요 키워드가 포함되면 점수 대폭 상승)
            for kw in keywords:
                if kw.lower() in doc.lower() or kw.lower() in metadata['source'].lower():
                    score += 0.5 # 키워드 매칭 시 가중치 부여
            
            scored_results.append({
                'score': score,
                'content': doc,
                'source': metadata['source']
            })

        # 3. 점수 순으로 재정렬하여 출력
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        for res in scored_results[:k]:
            print(f"점수: {res['score']:.4f} | 출처: {res['source']}")
            print(f"내용: {res['content'][:200]}...")
