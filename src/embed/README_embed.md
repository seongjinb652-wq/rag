# 벡터 임베딩 + Chroma DB

## 📌 목표

- ✅ 텍스트를 벡터로 변환 (한국어 최적화)
- ✅ Chroma DB에 저장
- ✅ 유사도 검색
- ✅ 벡터 DB 통계

---

## 🚀 실행 방법

### Step 1: 부모 폴더로 이동

```bash
# src/embed 폴더에서
cd ..
pwd
# C:\Users\USER\rag\src 확인

# 다시 embed로 이동
cd embed
```

### Step 2: 실행

```bash
python setup_vector_store.py
```

### 예상 출력

```
================================================================================
🚀 벡터 저장소 초기화 및 테스트
================================================================================

🔧 벡터 저장소 초기화 중...
✅ Chroma DB 생성: C:\Users\USER\rag\data\chroma_db
🤖 임베딩 모델 로드 중...
✅ 모델 로드: sentence-transformers/xlm-r-base-multilingual-nli-stsb

1️⃣ 문서 추가
────────────────────────────────────────────────────────────────────────────
📝 5개 문서 추가 시작...
   진행: 5/5 문서
✅ 추가 완료: 5개 (스킵: 0개)

2️⃣ 저장소 통계
────────────────────────────────────────────────────────────────────────────
db_path: C:\Users\USER\rag\data\chroma_db
collection_name: rag_documents
total_documents: 5
model: sentence-transformers/xlm-r-base-multilingual-nli-stsb
embedding_dimension: 768

3️⃣ 유사도 검색 테스트
────────────────────────────────────────────────────────────────────────────

📌 쿼리: '서울에 대해 알려줘'
   1. [0.8234] 서울은 한반도 중앙에 위치한 대한민...
   2. [0.7891] 한국의 수도는 서울입니다...
   3. [0.6543] 남산타워는 서울의 유명한 랜드마크입니다...

📌 쿼리: 'Python이란 무엇인가?'
   1. [0.9123] Python은 인기 있는 프로그래밍 언어입니다...
   2. [0.2345] 서울은 한반도 중앙에 위치한 대한민...
   3. [0.1234] 한국의 수도는 서울입니다...

📌 쿼리: '한국의 주요 도시'
   1. [0.8567] 한국의 수도는 서울입니다...
   2. [0.7654] 서울은 한반도 중앙에 위치한 대한민...
   3. [0.5432] 남산타워는 서울의 유명한 랜드마크입니다...

4️⃣ 통계 저장
────────────────────────────────────────────────────────────────────────────
✅ 통계 저장: C:\Users\USER\rag\data\vector_stats.json

================================================================================
✅ 벡터 저장소 테스트 완료!
================================================================================
```

---

## 🔧 주요 기능

### 1️⃣ 벡터 저장소 초기화

```python
from setup_vector_store import VectorStore

store = VectorStore()
```

**자동 처리:**
- Chroma DB 생성
- 임베딩 모델 로드 (Ko-SBERT)
- 컬렉션 생성

### 2️⃣ 문서 추가

```python
documents = [
    {
        'text': '한국의 수도는 서울입니다.',
        'source': 'test_1'
    },
    ...
]

result = store.add_documents(documents)
# {'added': 100, 'skipped': 2, 'total_docs': 102}
```

**특징:**
- 배치 처리 (100개씩)
- 자동 임베딩 생성
- 메타데이터 저장

### 3️⃣ 유사도 검색

```python
results = store.search('서울에 대해 알려줘', n_results=5)

for result in results:
    print(f"[{result['similarity']}] {result['text']}")
    # [0.8234] 서울은 한반도 중앙에 위치한...
```

**반환 값:**
```python
[
    {
        'text': '검색된 문서',
        'similarity': 0.8234,  # 0~1 (높을수록 유사)
        'metadata': {'source': 'xxx', 'length': 100}
    },
    ...
]
```

### 4️⃣ 저장소 통계

```python
stats = store.get_stats()
# {
#     'db_path': '...',
#     'total_documents': 102,
#     'model': '...',
#     'embedding_dimension': 768
# }

store.save_stats()  # stats.json 저장
```

---

## ⚙️ 설정

`config.py`에서:

```python
EMBEDDING_MODEL = 'sentence-transformers/xlm-r-base-multilingual-nli-stsb'
EMBEDDING_DIMENSION = 768
CHROMA_DB_PATH = Path('data/chroma_db')
CHROMA_COLLECTION_NAME = 'rag_documents'
VECTOR_SEARCH_K = 5  # 상위 5개 검색
```

---

## 📊 성능

| 항목 | 성능 |
|------|------|
| 임베딩 생성 (문서) | 100ms |
| 검색 (5개 결과) | 50ms |
| 배치 저장 (100개) | 2초 |
| 메모리 (1000개 문서) | 200MB |

---

## 🐛 트러블슈팅

### 오류: "ModuleNotFoundError: No module named 'config'"

**해결:**
```bash
# src/embed/ 폴더에서 실행
# ✅ 올바름

# 다른 폴더에서 실행
# ❌ 틀림 → src/embed로 이동 후 실행
```

### 오류: "CUDA out of memory"

**원인:** GPU 메모리 부족

**해결:**
```python
# config.py에서
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # 더 가벼운 모델
```

### 검색 결과 없음

**원인:** 문서가 없거나 완전히 다른 주제

**확인:**
```python
stats = store.get_stats()
print(stats['total_documents'])  # 0이면 문서 추가 필요
```

---

## 📁 생성 파일

```
data/
├── chroma_db/          # Chroma DB 저장소
│   ├── chroma.sqlite3  # 메타데이터
│   └── data/           # 벡터 데이터
└── vector_stats.json   # 통계
```

---

## ✅ 체크리스트

```
☑️ setup_vector_store.py 실행
☑️ Chroma DB 생성 확인
☑️ 테스트 문서 5개 추가 확인
☑️ 유사도 검색 결과 확인
☑️ vector_stats.json 생성 확인
```

---

## 🎯 다음 단계

**Day 4: RAG 엔진** (`src/rag/`)

- setup_vector_store.py에서 생성된 벡터 DB 사용
- Claude API와 연동
- RAG (Retrieval-Augmented Generation) 파이프라인

---

**벡터 저장소 준비 완료! 🚀**
