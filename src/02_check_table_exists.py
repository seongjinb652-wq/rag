# 02_confirm_txt.py
# 02_check_table_exists.py
from pathlib import Path

# 아까 확인하신 그 파일 경로
file_path = Path(r"C:/Users/USER/rag/src/data/text_converted/인도네시아 의료 사업성평가 보고서_20240330_1일 환자수 30명병원20개_b569c0.txt")

if file_path.exists():
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    print(f"📄 파일명: {file_path.name}")
    print("=" * 60)
    
    # 표 기호(|)가 포함된 줄 근처 20줄만 출력
    found = False
    for i, line in enumerate(lines):
        if "|" in line:
            print(f"[표 감지됨 - {i}행 부근]")
            # 앞뒤 맥락 포함 15줄 출력
            start = max(0, i-2)
            end = min(len(lines), i+15)
            print("".join(lines[start:end]))
            found = True
            break
            
    if not found:
        print("❓ 이 파일 앞부분에는 아직 표가 없습니다. 뒤쪽 페이지를 더 탐색해야 합니다.")
else:
    print("❌ 파일을 찾을 수 없습니다.")
