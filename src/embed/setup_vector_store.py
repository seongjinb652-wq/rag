#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
벡터 임베딩 + Chroma DB 저장
목표: 텍스트를 벡터로 변환 후 Chroma DB에 저장

기능:
- 한국어 최적화 임베딩 (Ko-SBERT)
- Chroma DB 초기화
- 문서 추가 및 검색
- 벡터 유사도 계산

실행: python setup_vector_store.py
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 부모 폴더에서 config 임포트
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import importlib.util
spec = importlib.util.spec_from_file_location("config", config_file)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)
Settings = config_module.Settings

class VectorStore:
    """벡터 저장소 - Chroma DB"""
    
    def __init__(self):
        """초기화"""
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        logger.info("🔧 벡터 저장소 초기화 중...")
        
        # Chroma DB 초기화
        self.db_path = str(Settings.CHROMA_DB_PATH)
        Settings.CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # 기존 컬렉션이 있으면 삭제 후 재생성 (테스트 모드)
        try:
            self.client.delete_collection(name=Settings.CHROMA_COLLECTION_NAME)
            logger.info(f"기존 컬렉션 삭제: {Settings.CHROMA_COLLECTION_NAME}")
        except:
            pass
        
        # 새 컬렉션 생성
        self.collection = self.client.get_or_create_collection(
            name=Settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"✅ Chroma DB 생성: {self.db_path}")
        
        # 임베딩 모델 로드
        logger.info("🤖 임베딩 모델 로드 중...")
        self.model = SentenceTransformer(Settings.EMBEDDING_MODEL)
        logger.info(f"✅ 모델 로드: {Settings.EMBEDDING_MODEL}")
        
        self.doc_count = 0
    
    def add_documents(self, documents: List[Dict]) -> Dict:
        """문서를 벡터로 변환 후 DB에 추가"""
        
        logger.info(f"📝 {len(documents)}개 문서 추가 시작...")
        
        if not documents:
            logger.warning("추가할 문서 없음")
            return {'added': 0, 'skipped': 0}
        
        # 배치 처리 (100개씩)
        batch_size = 100
        total_added = 0
        total_skipped = 0
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            ids = []
            texts = []
            embeddings = []
            metadatas = []
            
            for idx, doc in enumerate(batch):
                text = doc.get('text', '')
                source = doc.get('source', 'unknown')
                
                if not text.strip():
                    total_skipped += 1
                    continue
                
                # 임베딩 생성
                embedding = self.model.encode(text, convert_to_numpy=True)
                
                doc_id = f"doc_{self.doc_count}_{idx}"
                ids.append(doc_id)
                texts.append(text)
                embeddings.append(embedding.tolist())
                metadatas.append({
                    'source': source,
                    'length': len(text)
                })
                
                total_added += 1
            
            # 배치 추가
            if ids:
                self.collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas
                )
                
                progress = min(i + batch_size, len(documents))
                logger.info(f"   진행: {progress}/{len(documents)} 문서")
            
            self.doc_count += batch_size
        
        logger.info(f"✅ 추가 완료: {total_added}개 (스킵: {total_skipped}개)")
        
        return {
            'added': total_added,
            'skipped': total_skipped,
            'total_docs': self.collection.count()
        }
    
    def search(self, query: str, n_results: int = 5) -> List[Dict]:
        """유사 문서 검색"""
        
        logger.info(f"🔍 검색: '{query}'")
        
        try:
            # 쿼리 임베딩
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            
            # 유사 문서 검색
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results
            )
            
            # 결과 정렬
            documents = []
            if results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 0
                    similarity = 1 - distance  # cosine 거리를 유사도로 변환
                    
                    documents.append({
                        'text': doc,
                        'similarity': round(similarity, 4),
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {}
                    })
            
            logger.info(f"✅ 검색 완료: {len(documents)}개 결과")
            
            return documents
        
        except Exception as e:
            logger.error(f"❌ 검색 실패: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """저장소 통계"""
        
        count = self.collection.count()
        
        stats = {
            'db_path': self.db_path,
            'collection_name': Settings.CHROMA_COLLECTION_NAME,
            'total_documents': count,
            'model': Settings.EMBEDDING_MODEL,
            'embedding_dimension': Settings.EMBEDDING_DIMENSION
        }
        
        return stats
    
    def save_stats(self, file_path: Path = None):
        """통계 저장"""
        
        if file_path is None:
            file_path = Settings.DATA_DIR / 'vector_stats.json'
        
        stats = self.get_stats()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 통계 저장: {file_path}")
        
        return stats


def main():
    """테스트 실행"""
    
    print("\n" + "="*80)
    print("🚀 벡터 저장소 초기화 및 테스트")
    print("="*80)
    
    # 벡터 저장소 생성
    store = VectorStore()
    
    # 테스트 문서
    test_documents = [
        {
            'text': '한국의 수도는 서울입니다.',
            'source': 'test_1'
        },
        {
            'text': '서울은 한반도 중앙에 위치한 대한민국의 정치, 경제, 문화의 중심지입니다.',
            'source': 'test_2'
        },
        {
            'text': '남산타워는 서울의 유명한 랜드마크입니다.',
            'source': 'test_3'
        },
        {
            'text': '한강은 서울을 가로질러 흐르는 중요한 강입니다.',
            'source': 'test_4'
        },
        {
            'text': 'Python은 인기 있는 프로그래밍 언어입니다.',
            'source': 'test_5'
        },
    ]
    
    # 문서 추가
    print("\n1️⃣ 문서 추가")
    print("-" * 80)
    result = store.add_documents(test_documents)
    print(f"추가됨: {result['added']}, 스킵: {result['skipped']}")
    
    # 통계
    print("\n2️⃣ 저장소 통계")
    print("-" * 80)
    stats = store.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # 검색 테스트
    print("\n3️⃣ 유사도 검색 테스트")
    print("-" * 80)
    
    queries = [
        '서울에 대해 알려줘',
        'Python이란 무엇인가?',
        '한국의 주요 도시'
    ]
    
    for query in queries:
        print(f"\n📌 쿼리: '{query}'")
        results = store.search(query, n_results=3)
        
        for i, result in enumerate(results, 1):
            print(f"   {i}. [{result['similarity']}] {result['text'][:50]}...")
    
    # 통계 저장
    print("\n4️⃣ 통계 저장")
    print("-" * 80)
    store.save_stats()
    
    print("\n" + "="*80)
    print("✅ 벡터 저장소 테스트 완료!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
