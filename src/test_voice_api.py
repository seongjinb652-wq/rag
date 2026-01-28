import requests

# FastAPI 서버 주소
URL = "http://127.0.0.1:8000/voice"

def test_voice(file_path):
    print(f"\n🚀 {file_path} 테스트 중...")
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'audio/wav')}
        response = requests.post(URL, files=files)
        
    if response.status_code == 200:
        res = response.json()
        print(f"🎙️ 인식된 텍스트: {res['original_text']}")
        print(f"🔍 교정된 쿼리: {res['refined_query']}")
        print(f"🤖 답변: {res['answer'][:100]}...") # 답변이 길 수 있어 앞부분만 출력
        print(f"📂 출처: {res['sources']}")
    else:
        print(f"❌ 실패: {response.status_code}, {response.text}")

# 생성된 5개 파일 테스트
for i in range(1, 6):
    test_voice(f"test_audio/test_q{i}.wav")
