# 02_confirm_txt.py
import os
from pathlib import Path

# 변환된 파일이 저장된 경로
TXT_DIR = Path(r"C:/Users/USER/rag/src/data/text_converted")

# '정동'이나 '사업성'이 들어간 파일 하나를 골라 내용 확인
target_files = [f for f in os.listdir(TXT_DIR) if '정동' in f or '사업성' in f]

if target_files:
    sample_path = TXT_DIR / target_files[0]
    print(f"✅ 검증 파일: {sample_path.name}")
    with open(sample_path, 'r', encoding='utf-8') as f:
        content = f.read()
        # 마크다운 표 기호(|)가 있는지, PDT 보정이 되었는지 확인
        print("-" * 50)
        print(content[:1500]) # 앞부분 1500자만 출력
        print("-" * 50)
else:
    print("❌ 변환된 파일을 찾을 수 없습니다. 경로를 확인하세요.")
