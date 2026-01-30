import requests
import os
from config import Settings # 새 추가

# FastAPI 서버 주소 연동
# URL = "http://127.0.0.1:8000/voice"
URL = f"{Settings.API_BASE_URL}{Settings.ENDPOINT_VOICE}"

def test_voice(file_path):
    print(f"\n🚀 {file_path} 테스트 중...")
    if not os.path.exists(file_path):
        print(f"❌ 파일 없음: {file_path}")
        return

    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'audio/wav')}
        response = requests.post(URL, files=files)
        
    if response.status_code == 200:
        res = response.json()
        print(f"🎙️ 인식: {res['original_text']}")
        print(f"🔍 교정: {res.get('refined_query', 'N/A')}")
        print(f"🤖 답변: {res['answer'][:100]}...")
        # v5 표준 출처 확인
        print(f"📂 출처: {res['sources']}")
    else:
        print(f"❌ 실패: {response.status_code}")

if __name__ == "__main__":
    # 테스트 파일 경로 (Settings.DATA_DIR 기준 활용 가능)
    test_dir = "test_audio" 
    for i in range(1, 6):
        test_voice(f"{test_dir}/test_q{i}.wav")
