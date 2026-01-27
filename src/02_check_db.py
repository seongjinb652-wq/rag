#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import chromadb
from pathlib import Path

# 설정 (01번 파일과 동일하게 유지)
DB_PATH = Path(r"C:/Users/USER/rag/src/data/chroma_db")
COLLECTION_NAME = "indonesia_pdt_docs"

def check_database():
    print("\n" + "="*50)
    print("🔍 Chroma DB 저장 상태 확인")
    print("="*50)

    try:
        # 1. DB 클라이언트 연결
        client = chromadb.PersistentClient(path=str(DB_PATH))
        
        # 2. 컬렉션 가져오기
        collection = client.get_collection(name=COLLECTION_NAME)
        
        # 3. 전체 개수 확인
        count = collection.count()
        print(f"📈 총 저장된 청크 수: {count}개")

        if count > 0:
            # 4. 최근 저장된 데이터 3개만 미리보기 (peek)
            print("\n👀 데이터 샘플 미리보기 (최초 3개):")
            samples = collection.peek(3)
            
            for i in range(len(samples['ids'])):
                print(f"\n[{i+1}] ID: {samples['ids'][i]}")
                print(f"📂 출처: {samples['metadatas'][i].get('source', '알 수 없음')}")
                # 텍스트는 너무 길 수 있으니 100자만 출력
                content = samples['documents'][i].replace('\n', ' ')
                print(f"📝 내용: {content[:100]}...")
        else:
            print("⚠️ DB에 저장된 데이터가 없습니다.")

    except Exception as e:
        print(f"❌ DB 확인 중 에러 발생: {e}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    check_database()
