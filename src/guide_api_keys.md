# API 키 신청 가이드

## 📌 신청 우선순위

| 순서 | 서비스 | 시간 | 필수 | 비고 |
|------|--------|------|------|------|
| **1순위** | Claude API 키 | 5분 | ⭐⭐⭐ | 즉시 발급 |
| **2순위** | 네이버 클라우드 | 10분 | ⭐⭐⭐ | 즉시 발급 |
| **3순위** | Azure 계정 | 15분 | ⭐⭐ | 3주차 필요 |

---

## 1️⃣ Claude API 키 (5분, 필수)

### 📝 신청 방법

```
1. https://console.anthropic.com 방문
2. 상단 "Sign Up" 클릭
   또는
   https://www.anthropic.com/account/overview 에서 로그인

3. "Get API key" 클릭
4. "Create new secret key" 클릭
5. 키 복사 → 안전한 곳에 저장
```

### ✅ 발급 확인
```
키 형식: sk-ant-xxxxxxxxxxxxxxxxxxxxx
발급 속도: 즉시
사용 시작: 바로 가능
```

### 💳 무료 사용 가능?
```
- 신규 가입: $5 무료 크레딧 (약 50회 테스트 가능)
- 유료 전환: 필요시 결제정보 추가
- 테스트용: 충분함
```

**🔗 Claude API 콘솔:** https://console.anthropic.com

---

## 2️⃣ 네이버 클라우드 (10분, 필수)

### 📝 신청 방법

```
1. https://www.ncloud.com 방문
2. 상단 우측 "로그인" 클릭
   (또는 회원가입 필요: https://www.ncloud.com/mypage/member/join)

3. 대시보드 → "Products & Services"
4. "Object Storage" 검색
5. 서비스 신청 (무료 플랜 선택)
```

### 📦 Object Storage 설정

```
대시보드 → Object Storage → "My Page"

필요한 정보 수집:
1. Access Key ID
2. Secret Access Key  
3. Bucket 이름 (생성 필요)
4. 리전: kr-standard (서울)
```

### 🔑 Access Key 생성

```
1. 대시보드 → "My Page"
2. "Manage Authentication Key"
3. "Create new access key"
4. Access Key ID + Secret Access Key 복사 (보관 중요!)

주의: Secret Key는 발급 후 다시 볼 수 없음!
→ 복사 후 바로 안전하게 저장
```

### 🗂️ Bucket 생성

```
1. Object Storage 대시보드
2. "Create Bucket" 클릭
3. 이름: rag-chatbot-data (예시)
4. 리전: kr-standard
5. 생성 완료
```

**🔗 네이버 클라우드 콘솔:** https://console.ncloud.com

---

## 3️⃣ Azure 계정 (선택, 3주차 필요)

### 📝 신청 방법 (나중에)

```
1. https://azure.microsoft.com/en-us/free 방문
2. "Start free" 클릭
3. Microsoft 계정 로그인 (또는 생성)
4. 신분증/신용카드 인증 (무료 계정용)
5. $200 크레딧 획득 (1개월 유효)
```

### ⭐ 무료 플랜
```
- F1 Free Tier App Service: 월 730시간 무료
- 거의 24/7 운영 가능
- 3주 프로토타입: 완전 무료
```

**🔗 Azure 무료 계정:** https://azure.microsoft.com/en-us/free

---

## 📋 체크리스트

### ✅ 필수 (즉시)
```
☑️ Claude API 키 발급
   → sk-ant-xxxxx 형식
   
☑️ 네이버 클라우드 가입
   → Access Key ID
   → Secret Access Key
   → Bucket 이름
```

### ⏳ 선택 (나중에, 3주차 필요)
```
☐ Azure 계정 생성 (Day 12에 생성해도 됨)
```

---

## 🔐 발급받은 키 정리

다운로드 후 `.env` 파일에 저장할 정보:

```env
# Claude API
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# 네이버 클라우드
NAVER_ACCESS_KEY=your_access_key_id
NAVER_SECRET_KEY=your_secret_access_key
NAVER_BUCKET_NAME=rag-chatbot-data
NAVER_REGION=kr-standard
```

---

## ⚠️ 보안 주의사항

```
🔴 절대 하면 안 되는 것:
  ❌ GitHub에 키 업로드
  ❌ 공개 채팅에 키 공유
  ❌ 키를 소스코드에 하드코딩
  
✅ 해야 할 것:
  ☑️ .env 파일에만 저장
  ☑️ .gitignore에 .env 추가
  ☑️ 안전한 곳에 백업
```

---

**모든 키 발급이 완료되면 setup_environment.py 실행 준비 완료!** 🎉
