# make_test_voice.py
from gtts import gTTS
import os

# 테스트할 질문 리스트 (alias_map 검증용)
questions = [
    "제주 수소발전 및 PPH 사업 소개서 내용을 알려줘",
    "판매기업 승인방법 다양화 MP 발송은 어떻게 해?" ,
    "중입자 가속기 사업의 연면적은 어떻게 돼?",
    "호텔 위탁운영 계약과 에이치엠에이의 차이점을 설명해줘.",
    "이번 프로젝트의 알오아이 수치와 자본지출 내역 알려줘.",
    "비트코인을 활용한 에스티오 자산유동화 계획이 문서에 있어?",
    "인도네시아 현지 법인의 인허가 현황과 추진 일정 확인해줘."
]

os.makedirs("test_audio", exist_ok=True)

for i, q in enumerate(questions):
    tts = gTTS(text=q, lang='ko')
    filename = f"test_audio/test_q{i+1}.wav"
    tts.save(filename)
    print(f"✅ 생성 완료: {filename} ({q})")
