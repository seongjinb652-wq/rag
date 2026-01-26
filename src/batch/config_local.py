from pathlib import Path

class Settings:
    # 로컬 테스트용 디렉토리
    TARGET_DIR = Path(r"C:\Users\USER\Downloads\@@@인도네시아PDT암센터FS")

    # 상태 파일 저장 위치
    STATE_FILE = Path("batch_state_local.json")

    # 로그 디렉토리
    LOG_DIR = Path("logs")
    SUPPORTED_FORMATS = {'.pdf', '.docx', '.doc', '.pptx', '.txt'}
