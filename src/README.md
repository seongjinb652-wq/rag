핵심 기술 스택 변화
1. 문서 처리 파이프라인 (Document Processor)
v3: 파일 스캔 후 즉시 벡터화. 데이터 유실 시 전체 재스캔 필요.

v4: 청크 상단에 Source: [파일경로]와 구분선(---)을 강제로 삽입하여 LLM이 컨텍스트의 출처를 스스로 인지하도록 설계.

2. 벡터 저장 및 검색 (Vector Store & Search)
v3: d.metadata['source']를 통해 파일 경로 추적.

v4: 본문 파싱과 메타데이터 조회를 동시에 수행하는 이중 안전장치 도입. 이를 통해 📂 출처: [] 누락 문제 해결.

3. 배치 스케줄링 (Batch Scheduler)
v3: LocalBatchScheduler를 통해 로컬 디렉토리(TARGET_DIR)의 변경 사항(Size, Modified Time)을 감시.

v4: 상태 관리 로직을 API 서버와 통합하여 데이터 업데이트 편의성 극대화.


rag/
├── src/
│   ├── parse/          # [v3] 문서 파싱 엔진 (PDF, PPT, Word)
│   ├── embed/          # [v3] 벡터 임베딩 및 Chroma DB 설정
│   ├── batch/          # [v3] 로컬 배치 스케줄러 및 상태 관리
│   └── 07_voice_rag_api.py  # [v4] 통합 RAG 서비스 API (Voice + LLM)
├── logs/               # 실행 로그 및 배치 처리 리포트
└── data/               # Chroma DB 및 batch_state_local.json

🚀 실행 가이드 (How to Run)
본 시스템은 데이터 관리(v3)와 서비스 제공(v4)의 이원화된 구조로 운영됩니다.

1. 환경 설정 (Prerequisites)
시스템 실행 전 필요한 패키지를 설치하고, config.py의 경로 설정을 확인하십시오.

# 필수 패키지 설치
pip install -r requirements.txt

# OCR 기능 사용 시 Tesseract 설치 확인
# Windows: C:\Program Files\Tesseract-OCR\tesseract.exe

2. 데이터 관리 및 초기화 (v3 Legacy Tools)
"v3는 초기화" 원칙에 따라, 전체 문서를 처음부터 다시 인덱싱하거나 테스트할 때 사용합니다.

문서 처리 테스트 (Parsing Test)

python src/parse/setup_document_processor.py


벡터 저장소 초기화 (Vector Store Reset)

벡터 저장소 초기화 (Vector Store Reset)

Bash
python src/embed/setup_vector_store.py
주의: 기존 Chroma DB 컬렉션을 삭제하고 새롭게 생성합니다.

로컬 배치 스케줄러 실행 (Manual Sync)

Bash
python src/batch/local_batch_scheduler.py
로컬 디렉토리의 변경 사항을 감지하여 batch_state_local.json을 업데이트하고 누락된 문서를 DB에 반영합니다.

3. RAG 서비스 실행 (v4 Main Service)
"v4는 이어넣기" 원칙에 따라, 실시간 음성 대화 및 검색 서비스를 제공합니다.

통합 RAG 서버 실행

Bash
python src/07_voice_rag_api.py
주요 기능: FastAPI 기반 서버 구동, 실시간 음성 인식(STT) 연동, LLM 답변 생성 및 출처(Source) 정제 출력.

4. 워크플로우 (Daily Operation)
평상시 데이터 업데이트와 서비스 운영은 아래 순서를 권장합니다.

신규 문서 추가: 지정된 TARGET_DIR 폴더에 새 PDF/PPT/Docx 파일을 넣습니다.

데이터 동기화: local_batch_scheduler.py를 실행하여 v4 데이터 구조로 이어넣기를 수행합니다.

서비스 구동: 07_voice_rag_api.py 서버를 켜서 실시간 질문에 대응합니다.

출처 확인: 응답 메시지 하단의 📂 출처: [...] 목록을 통해 데이터 정합성을 검증합니다.
