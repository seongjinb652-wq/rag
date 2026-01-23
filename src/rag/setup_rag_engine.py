#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
RAG (Retrieval-Augmented Generation) 엔진
목표: 벡터 DB에서 문서 검색 후 Claude API로 답변 생성

기능:
- 벡터 DB에서 유사 문서 검색
- Claude API와 연동
- 컨텍스트 기반 답변 생성
- 검색 결과 및 답변 기록

실행: python setup_rag_engine.py
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import logging
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# config.py 파일 직접 로드 (절대경로)
PROJECT_ROOT = Path(__file__).parent.parent.parent
config_file = PROJECT_ROOT / 'config.py'

if not config_file.exists():
    raise FileNotFoundError(f"config.py를 찾을 수 없습니다: {config_file}")

# config.py를 동적으로 로드
import importlib.util
spec = importlib.util.spec_from_file_location("config", config_file)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

Settings = config_module.Settings


class RAGEngine:
    """RAG 엔진"""
    
    def __init__(self):
        """초기화"""
        import chromadb
        from anthropic import Anthropic
        
        logger.info("🔧 RAG 엔진 초기화 중...")
        
        # Chroma DB 연결
        db_path = str(Settings.CHROMA_DB_PATH)
        self.client_db = chromadb.PersistentClient(path=db_path)
        self.collection = self.client_db.get_or_create_collection(
            name=Settings.CHROMA_COLLECTION_NAME
        )
        
        logger.info(f"✅ Chroma DB 연결: {db_path}")
        
        # Claude API 클라이언트
        self.client_llm = Anthropic(api_key=Settings.ANTHROPIC_API_KEY)
        logger.info(f"✅ Claude API 연결: {Settings.ANTHROPIC_MODEL}")
        
        # 임베딩 모델
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(Settings.EMBEDDING_MODEL)
        logger.info(f"✅ 임베딩 모델 로드")
        
        # 대화 히스토리
        self.conversation_history = []
    
    def retrieve_documents(self, query: str, n_results: int = None) -> List[Dict]:
        """유사 문서 검색"""
        
        if n_results is None:
            n_results = Settings.VECTOR_SEARCH_K
        
        logger.info(f"🔍 검색 시작: '{query}'")
        
        try:
            # 쿼리 임베딩
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            
            # 유사 문서 검색
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results
            )
            
            documents = []
            if results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 0
                    similarity = 1 - distance
                    
                    documents.append({
                        'text': doc,
                        'similarity': round(similarity, 4),
                        'source': results['metadatas'][0][i].get('source', 'unknown')
                            if results['metadatas'] else 'unknown'
                    })
            
            logger.info(f"✅ {len(documents)}개 문서 검색됨")
            
            return documents
        
        except Exception as e:
            logger.error(f"❌ 검색 실패: {e}")
            return []
    
    def build_context(self, documents: List[Dict]) -> str:
        """검색 결과로부터 컨텍스트 생성"""
        
        if not documents:
            return "관련 문서를 찾을 수 없습니다."
        
        context = "### 참고 자료\n\n"
        
        for i, doc in enumerate(documents, 1):
            context += f"**문서 {i}** (유사도: {doc['similarity']})\n"
            context += f"출처: {doc['source']}\n"
            context += f"내용: {doc['text'][:200]}...\n\n"
        
        return context
    
    def generate_answer(self, query: str, context: str) -> str:
        """Claude API로 답변 생성"""
        
        logger.info("🤖 답변 생성 중...")
        
        # 시스템 프롬프트
        system_prompt = """당신은 유능한 AI 어시스턴트입니다.
사용자의 질문에 대해 제공된 참고 자료를 바탕으로 정확하고 자세한 답변을 제공합니다.

### 규칙:
1. 참고 자료에 있는 정보를 우선적으로 사용
2. 모르는 것은 "관련 정보를 찾을 수 없습니다"라고 명시
3. 명확하고 구조화된 답변 제공
4. 필요시 출처 언급"""
        
        # 메시지 준비
        user_message = f"{context}\n\n### 질문:\n{query}"
        
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            # Claude API 호출
            response = self.client_llm.messages.create(
                model=Settings.ANTHROPIC_MODEL,
                max_tokens=Settings.MAX_TOKENS,
                system=system_prompt,
                messages=self.conversation_history
            )
            
            answer = response.content[0].text
            
            # 대화 히스토리에 추가
            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })
            
            logger.info("✅ 답변 생성 완료")
            
            return answer
        
        except Exception as e:
            logger.error(f"❌ 답변 생성 실패: {e}")
            return f"오류: {str(e)}"
    
    def query(self, question: str, verbose: bool = True) -> Dict:
        """전체 RAG 파이프라인"""
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 RAG 파이프라인 시작")
        logger.info(f"{'='*80}")
        
        start_time = datetime.now()
        
        # 1. 문서 검색
        documents = self.retrieve_documents(question)
        
        # 2. 컨텍스트 생성
        context = self.build_context(documents)
        
        # 3. 답변 생성
        answer = self.generate_answer(question, context)
        
        # 4. 결과 정리
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            'question': question,
            'documents': documents,
            'context': context,
            'answer': answer,
            'elapsed_time': round(elapsed_time, 2),
            'doc_count': len(documents)
        }
        
        # 5. 출력
        if verbose:
            print("\n" + "="*80)
            print("📌 질문")
            print("="*80)
            print(question)
            
            print("\n" + "="*80)
            print(f"📚 검색된 문서 ({len(documents)}개)")
            print("="*80)
            for i, doc in enumerate(documents, 1):
                print(f"\n{i}. [{doc['similarity']}] {doc['source']}")
                print(f"   {doc['text'][:100]}...")
            
            print("\n" + "="*80)
            print("💡 답변")
            print("="*80)
            print(answer)
            
            print("\n" + "="*80)
            print(f"⏱️ 소요 시간: {elapsed_time:.2f}초")
            print("="*80 + "\n")
        
        return result
    
    def save_results(self, results: List[Dict], file_path: Path = None):
        """결과 저장"""
        
        if file_path is None:
            file_path = Settings.LOGS_DIR / f"rag_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 결과 저장: {file_path}")


def main():
    """테스트 실행"""
    
    print("\n" + "="*80)
    print("🚀 RAG 엔진 테스트")
    print("="*80)
    
    # RAG 엔진 초기화
    rag = RAGEngine()
    
    # 테스트 쿼리
    test_queries = [
        "서울에 대해 알려줘",
        "Python이 무엇인가요?",
        "한강은 어떤 강인가요?"
    ]
    
    results = []
    
    for query in test_queries:
        result = rag.query(query, verbose=True)
        results.append(result)
    
    # 결과 저장
    rag.save_results(results)
    
    print("\n" + "="*80)
    print("✅ RAG 엔진 테스트 완료!")
    print(f"처리된 질문: {len(results)}개")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
