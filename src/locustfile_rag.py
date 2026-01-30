"""
RAG 지식베이스 서비스 부하 테스트
- 2명의 동시 사용자 시뮬레이션
- 20초 대기 간격
- LLM 응답: 8초 이내 목표 (RAG 검색 포함)
"""

from locust import HttpUser, task, between
import time
import random

class RAGUser(HttpUser):
    # 20초 고정 대기 (사용자 요구사항 반영)
    wait_time = between(20, 20)  
    
    def on_start(self):
        """사용자 시작 시 초기화 (로그인이 없으므로 출력만 수행)"""
        self.username = f"tester_{random.randint(1, 100)}"
        print(f"[{time.strftime('%H:%M:%S')}] {self.username} 부하 테스트 시작")
    
    @task(1)
    def rag_query_process(self):
        """RAG 질의 테스트 (가중치 1)"""
        # 현재 DB(11만 청크)에 특화된 질문 리스트
        questions = [
            "인도네시아 스마트 시티 프로젝트에 대해 알려줘",
            "부동산 개발 사업 타당성 검토 시 주요 고려사항은?",
            "반려동물 관련 사업 아이템 사례가 있니?",
            "Banten Global Smart City의 재무 구조는 어때?",
            "헬스케어 관련 신사업 전략 수립 사례를 들어줘",
            "FS(예비 타당성 조사)의 일반적인 절차가 뭐야?"
        ]
        
        # 현재 API 규격에 맞춘 페이로드
        payload = {
            "message": random.choice(questions)
        }
        
        start_time = time.time()
        
        # 07_voice_rag_api_v5.py의 /query 엔드포인트 호출
        with self.client.post("/query", 
                             json=payload,
                             catch_response=True,
                             timeout=15) as response:
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                # LLM 응답 목표: 8초 (RAG 검색 성능 포함)
                if elapsed > 8.0:
                    response.failure(f"LLM 응답 시간 초과: {elapsed:.2f}초 (목표: 8초 이내)")
                    print(f"❌ {self.username} 지연 발생: {elapsed:.2f}초")
                else:
                    response.success()
                    print(f"✅ {self.username} 응답 성공: {elapsed:.2f}초")
            else:
                response.failure(f"HTTP {response.status_code} 에러 발생")
                print(f"🔥 {self.username} 서버 에러: {response.status_code}")

# 실행 방법:
# 1. 터미널에서: locust -f locustfile_rag.py --host=http://localhost:8000
# 2. 브라우저에서: http://localhost:8089 접속
# 3. 설정: Number of users: 2 / Spawn rate: 1
