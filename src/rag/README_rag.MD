# RAG 엔진

## 📌 목표

- ✅ 벡터 DB에서 유사 문서 검색
- ✅ Claude API와 연동
- ✅ 컨텍스트 기반 답변 생성
- ✅ 대화 히스토리 관리

---

## 🚀 실행 방법

### 사전 준비

1. **Day 3 완료** (벡터 DB 생성됨)
```bash
python src/embed/setup_vector_store.py
```

2. **pip uninstall config -y** (이전 오류 제거)

### Step 1: 실행

```bash
cd src/rag
python setup_rag_engine.py
```

### 예상 출력

```
================================================================================
🚀 RAG 엔진 테스트
================================================================================

================================================================================
📌 질문
================================================================================
서울에 대해 알려줘

================================================================================
📚 검색된 문서 (3개)
================================================================================

1. [0.8234] test_2
   서울은 한반도 중앙에 위치한 대한민국의 정치, 경제...

2. [0.7891] test_1
   한국의 수도는 서울입니다...

3. [0.6543] test_3
   남산타워는 서울의 유명한 랜드마크입니다...

================================================================================
💡 답변
================================================================================

서울에 대해 설명하겠습니다:

1. **위치와 역할**
   - 서울은 한반도 중앙에 위치
   - 대한민국의 수도
   - 정치, 경제, 문화의 중심지

2. **주요 특징**
   - 남산타워 등 유명한 랜드마크 보유
   - 한강이 가로질러 흐름
   - 대규모 도시 인프라

3. **문화 및 관광**
   - 다양한 문화 시설 보유
   - 한국의 대표 관광지

================================================================================
⏱️ 소요 시간: 2.34초
================================================================================
```

---

## 🔧 주요 기능

### 1️⃣ 문서 검색

```python
from setup_rag_engine import RAGEngine

rag = RAGEngine()

# 유사 문서 검색
documents = rag.retrieve_documents(
    query="서울에 대해 알려줘",
    n_results=5
)

for doc in documents:
    print(f"[{doc['similarity']}] {doc['text']}")
```

### 2️⃣ 컨텍스트 생성

```python
context = rag.build_context(documents)
# 검색 결과를 Claude에 전달할 형식으로 변환
```

### 3️⃣ 답변 생성

```python
answer = rag.generate_answer(
    query="서울에 대해 알려줘",
    context=context
)
print(answer)
```

### 4️⃣ 전체 파이프라인

```python
result = rag.query(
    question="서울에 대해 알려줘",
    verbose=True
)

# result = {
#     'question': '...',
#     'documents': [...],
#     'context': '...',
#     'answer': '...',
#     'elapsed_time': 2.34,
#     'doc_count': 3
# }
```

---

## ⚙️ 설정

`config.py`에서:

```python
VECTOR_SEARCH_K = 5        # 검색할 문서 수
MAX_TOKENS = 1024          # 답변 최대 길이
ANTHROPIC_MODEL = 'claude-3-5-sonnet-20241022'
ANTHROPIC_API_KEY = 'sk-ant-...'
```

---

## 📊 성능

| 항목 | 시간 |
|------|------|
| 문서 검색 | 50ms |
| Claude API 호출 | 2~3초 |
| 전체 파이프라인 | 2~3초 |

---

## 🔄 대화 흐름

```
사용자 질문
    ↓
1️⃣ 벡터 임베딩 생성
    ↓
2️⃣ 유사 문서 검색 (Chroma DB)
    ↓
3️⃣ 컨텍스트 생성
    ↓
4️⃣ Claude API 호출
    ↓
5️⃣ 답변 생성
    ↓
대화 히스토리 저장
```

---

## 💾 결과 저장

```python
results = [
    rag.query("질문1"),
    rag.query("질문2"),
    rag.query("질문3")
]

rag.save_results(results)
# logs/rag_results_20250123_143052.json 생성
```

---

## 🐛 트러블슈팅

### 오류: "config.py를 찾을 수 없습니다"

**확인:**
```bash
# 프로젝트 구조
rag/
├── config.py        ← 여기
├── requirements.txt
└── src/
    ├── env/
    ├── parse/
    ├── embed/
    └── rag/          ← 현재 위치
```

### 오류: "Chroma DB 연결 실패"

**원인:** Day 3 미완료

**해결:**
```bash
python src/embed/setup_vector_store.py
```

### 답변 생성 느림

**원인:** Claude API 응답 대기

**확인:**
```python
result = rag.query(question, verbose=True)
print(f"소요 시간: {result['elapsed_time']}초")
```

---

## ✅ 체크리스트

```
☑️ pip uninstall config -y (중요!)
☑️ Day 3 완료 (벡터 DB 생성)
☑️ setup_rag_engine.py 실행
☑️ 답변이 정상적으로 생성되는지 확인
☑️ 결과 JSON 파일 생성 확인
```

---

## 🎯 다음 단계

**Day 5: 웹 UI** (`src/web/`)

- Streamlit으로 사용자 인터페이스 구축
- 실시간 질문/답변
- 검색 결과 시각화

---

**RAG 엔진 준비 완료! 🚀**
