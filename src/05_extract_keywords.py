import os
from collections import Counter
import pandas as pd
from kiwipiepy import Kiwi
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv

# .env 로드
load_dotenv()

# 경로 설정 (사용자님 환경 유지)
DB_PATH = r"C:/Users/USER/rag/src/data/chroma_db"
COLLECTION_NAME = "indonesia_pdt_docs"
OUTPUT_FILE = "top_300_keywords.csv"

def extract_keywords():
    print("🚀 키워드 분석 엔진 가동 중...")
    
    # 1. 형태소 분석기(Kiwi) 초기화
    kiwi = Kiwi()
    
    # 2. DB 연결 (기존 데이터 로드)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vector_db = Chroma(
        persist_directory=DB_PATH,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )
    
    # 3. 데이터 총 개수 확인
    total_count = vector_db._collection.count()
    print(f"📊 총 데이터 유닛(Chunks): {total_count}개")
    
    # 4. 배치 단위로 텍스트 추출 및 단어 카운트
    word_counter = Counter()
    batch_size = 500  # 메모리 보호를 위해 500개씩 처리
    
    print(f"🔍 단어 빈도 분석 시작 (Batch Size: {batch_size})...")
    
    for i in range(0, total_count, batch_size):
        # DB에서 텍스트 데이터 가져오기 (offset 활용)
        results = vector_db._collection.get(
            limit=batch_size,
            offset=i,
            include=["documents"]
        )
        
        batch_texts = results.get("documents", [])
        
        for text in batch_texts:
            # 명사(Noun)만 추출 (길이 2자 이상)
            tokens = kiwi.tokenize(text)
            nouns = [t.form for t in tokens if t.tag.startswith('N') and len(t.form) > 1]
            word_counter.update(nouns)
            
        if (i // batch_size) % 10 == 0 or (i + batch_size) >= total_count:
            current_progress = min(i + batch_size, total_count)
            print(f"⏳ 진행률: {current_progress} / {total_count} ({current_progress/total_count*100:.1f}%)")

    # 5. 상위 300개 추출
    top_300 = word_counter.most_common(300)
    
    # 6. 결과 저장 및 출력
    df = pd.DataFrame(top_300, columns=['Keyword', 'Frequency'])
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    
    print("\n" + "="*30)
    print(f"🏁 분석 완료! 상위 10개 키워드:")
    print(df.head(10))
    print(f"\n📂 전체 리스트가 '{OUTPUT_FILE}'로 저장되었습니다.")
    print("="*30)

if __name__ == "__main__":
    extract_keywords()
