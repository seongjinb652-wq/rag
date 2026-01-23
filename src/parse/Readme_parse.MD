#  문서 처리 파이프라인

## 📌 목표

- ✅ PDF 파일 파싱 (텍스트 + OCR)
- ✅ PowerPoint 슬라이드 추출
- ✅ Word 문서 파싱
- ✅ 이미지 OCR 처리
- ✅ 텍스트 청크 분할 (512 토큰 기준)

---

## 🚀 실행 방법

### Step 1: Tesseract OCR 설치 (선택)

**Windows:**
```bash
# https://github.com/UB-Mannheim/tesseract/wiki 에서 설치
# 또는 chocolatey:
choco install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**Mac:**
```bash
brew install tesseract
```

### Step 2: 테스트 파일 생성

`data/downloads/` 폴더에 테스트 파일 넣기:
- `sample.pdf`
- `sample.pptx`
- `sample.docx`
- `sample.txt`
- `sample.jpg` (이미지 파일)

### Step 3: 실행

```bash
cd src/parse/
python setup_document_processor.py
```

### 예상 출력

```
================================================================================
📚 문서 처리 시작
================================================================================

📕 PDF 처리: sample.pdf
   진행: 10/50 페이지
   진행: 20/50 페이지
   진행: 30/50 페이지
   진행: 40/50 페이지
   진행: 50/50 페이지
✅ PDF 완료: 50페이지 추출

📊 PPT 처리: sample.pptx
   진행: 10/25 슬라이드
   진행: 20/25 슬라이드
✅ PPT 완료: 25슬라이드 추출

📄 Word 처리: sample.docx
   진행: 100/250 단락
   진행: 200/250 단락
✅ Word 완료: 250단락 추출

🖼️ 이미지 OCR: sample.jpg
✅ OCR 완료: 1250 글자

================================================================================
📊 처리 결과
================================================================================
총 파일: 5
성공: 5
실패: 0
생성된 청크: 450
형식별: {'.pdf': 1, '.pptx': 1, '.docx': 1, '.jpg': 1}
소요 시간: 12.45초
================================================================================

✅ 문서 처리 완료!
   처리된 청크: 450
```

---

## 📁 파일 구조

```
src/parse/
├── setup_document_processor.py  ← 메인 파일 (이 파일)
└── README_parse.md              ← 이 문서
```

---

## 🔧 주요 기능

### 1️⃣ PDF 처리

```python
from setup_document_processor import DocumentProcessor

processor = DocumentProcessor()
pages = processor.process_pdf(Path("sample.pdf"))
# 페이지별 텍스트 추출
```

**특징:**
- 페이지별 분리
- 이미지 포함 시 OCR 자동 적용
- 진행 상황 표시

### 2️⃣ PPT 처리

```python
slides = processor.process_pptx(Path("sample.pptx"))
# 슬라이드별 텍스트 추출
```

**특징:**
- 슬라이드 번호 자동 포함
- 텍스트 박스만 추출 (이미지 제외)

### 3️⃣ Word 처리

```python
paragraphs = processor.process_docx(Path("sample.docx"))
# 단락별 텍스트 추출
```

**특징:**
- 단락 단위 분리
- 테이블도 추출

### 4️⃣ 이미지 OCR

```python
text = processor.process_image(Path("sample.jpg"))
# Tesseract로 한글 + 영문 인식
```

**특징:**
- 한글 + 영문 동시 인식
- 회전된 문서 자동 정정 (angle_cls)

### 5️⃣ 청크 분할

```python
chunks = processor.chunk_text(
    text="긴 문서...",
    source="sample.pdf"
)
# 512 토큰 기준, 50 토큰 겹침
```

**청크 구조:**
```python
{
    'text': '첫 512개 토큰...',
    'source': 'sample.pdf',
    'tokens': 512
}
```

---

## ⚙️ 설정

`config.py`에서 조정 가능:

```python
CHUNK_SIZE = 512      # 청크 크기 (토큰)
CHUNK_OVERLAP = 50    # 청크 겹침 (토큰)
```

---

## 🐛 트러블슈팅

### OCR 실패: "Tesseract not found"

**해결:**
```bash
# Windows
# C:\Program Files\Tesseract-OCR 확인

# Python에서 경로 설정:
pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### PDF 처리 느림

**원인:** 대용량 PDF (1000+ 페이지)

**해결:**
```python
# Day 6 배치에서 페이지 범위 설정 가능
# 예: 처음 100페이지만 처리
```

### 메모리 부족

**원인:** 매우 큰 파일들

**해결:**
```python
# config.py에서 조정
CHUNK_SIZE = 256  # 반으로 줄임
```

---

## 📊 성능 지표

| 파일형 | 처리 속도 | 메모리 |
|--------|---------|--------|
| PDF (50페이지) | 2-3초 | 50MB |
| PPT (25슬라이드) | 1-2초 | 30MB |
| Word (250단락) | 1초 | 20MB |
| 이미지 (OCR) | 2-3초 | 100MB |

---

## ✅ Day 2 체크리스트

```
☑️ setup_document_processor.py 실행
☑️ 샘플 파일로 테스트
☑️ 모든 형식 정상 처리 확인
☑️ 청크 생성 확인
```

---

## 🎯 다음 단계 (Day 3)

Day 3: 벡터 임베딩 + Chroma DB

```
src/embed/
├── setup_vector_store.py
└── vector_store.py
```

**Day 2 완료 후 Day 3 시작!** 🚀
