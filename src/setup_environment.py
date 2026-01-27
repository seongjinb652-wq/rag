#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Day 1: 환경설정 + 네이버 클라우드 연결 테스트
목표: Python 3.10 환경 구축 및 네이버 클라우드 API 정상 작동 확인

실행: python setup_environment.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 프로젝트 경로
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / 'data'
LOGS_DIR = PROJECT_ROOT / 'logs'

# 디렉토리 생성
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# .env 파일 로드
env_file = PROJECT_ROOT / '.env'
if not env_file.exists():
    logger.error("❌ .env 파일이 없습니다!")
    logger.info("📝 .env.example을 .env로 복사하세요: cp .env.example .env")
    sys.exit(1)

load_dotenv(env_file)


class EnvironmentChecker:
    """환경 및 의존성 확인"""
    
    def __init__(self):
        self.checks = {
            'python_version': False,
            'packages': False,
            'env_vars': False,
            'directories': False,
            'naver_cloud': False
        }
    
    def check_python_version(self):
        """Python 3.10 버전 확인"""
        print("\n" + "="*80)
        print("1️⃣ Python 버전 확인")
        print("="*80)
        
        py_version = sys.version_info
        py_version_str = f"{py_version.major}.{py_version.minor}.{py_version.micro}"
        
        print(f"설치된 Python: {py_version_str}")
        
        if py_version.major == 3 and py_version.minor == 10:
            print("✅ Python 3.10 확인됨")
            self.checks['python_version'] = True
            return True
        else:
            print(f"❌ Python 3.10 필요 (현재: {py_version_str})")
            print("   설치: python.org에서 3.10.13 다운로드")
            return False
    
    def check_packages(self):
        """필수 패키지 확인"""
        print("\n" + "="*80)
        print("2️⃣ 필수 패키지 확인")
        print("="*80)
        
        required_packages = [
            'dotenv',
            # 'boto3',  # ❌ 제거 대상
            'requests',
            'PyPDF2',
            'pptx',
            'docx',
        ]
        
        missing = []
        for pkg in required_packages:
            try:
                __import__(pkg if pkg != 'pptx' else 'pptx',
                          pkg if pkg != 'docx' else 'docx')
                print(f"✅ {pkg}")
            except ImportError:
                print(f"❌ {pkg} 미설치")
                missing.append(pkg)
        
        if missing:
            print(f"\n설치 명령: pip install -r requirements.txt")
            return False
        else:
            print("\n✅ 모든 필수 패키지 설치됨")
            self.checks['packages'] = True
            return True
    
    def check_env_variables(self):
        """환경 변수 확인"""
        print("\n" + "="*80)
        print("3️⃣ 환경 변수 확인")
        print("="*80)
        
        required_vars = {
            # 'ANTHROPIC_API_KEY': 'Claude API 키',              # 소규모 프로젝트 비용 문제로 수동 다운로드. 대형 대비 남겨둠.
            # 'NAVER_ACCESS_KEY': '네이버 클라우드 Access Key',   # 소규모 프로젝트 비용 문제로 수동 다운로드. 대형 대비 남겨둠.
            # 'NAVER_SECRET_KEY': '네이버 클라우드 Secret Key',   # 소규모 프로젝트 비용 문제로 수동 다운로드. 대형 대비 남겨둠.
            # 'NAVER_BUCKET_NAME': '네이버 클라우드 Bucket 이름',  # 소규모 프로젝트 비용 문제로 수동 다운로드. 대형 대비 남겨둠.
            # 'NAVER_REGION': '네이버 클라우드 리전',              # 소규모 프로젝트 비용 문제로 수동 다운로드. 대형 대비 남겨둠.
        }
        
        missing = []
        for var, desc in required_vars.items():
            value = os.getenv(var)
            if value:
                # 민감한 정보는 마스킹
                if 'KEY' in var:
                    masked = value[:5] + '*' * (len(value) - 8) + value[-3:]
                    print(f"✅ {var}: {masked}")
                else:
                    print(f"✅ {var}: {value}")
            else:
                print(f"❌ {var} 미설정 ({desc})")
                missing.append(var)
        
        if missing:
            print(f"\n❌ 설정되지 않은 변수: {', '.join(missing)}")
            print("📝 .env 파일에서 설정하세요")
            return False
        else:
            print("\n✅ 모든 환경 변수 설정됨")
            self.checks['env_vars'] = True
            return True
    
    def check_directories(self):
        """필요한 디렉토리 확인/생성"""
        print("\n" + "="*80)
        print("4️⃣ 디렉토리 구조 확인")
        print("="*80)
        
        required_dirs = {
            'data': DATA_DIR,
            'data/downloads': DATA_DIR / 'downloads',
            'logs': LOGS_DIR,
        }
        
        for name, path in required_dirs.items():
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ {name}: {path}")
        
        self.checks['directories'] = True
        return True

    def check_naver_cloud(self):                           
        """네이버 클라우드 연결 테스트 (비활성화)""" # ❌ 현재 프로젝트에서는 사용하지 않음 
        pass
        ''' # 소규모 프로젝트 비용 문제로 수동 다운로드. 대형 대비 남겨둠
        print("\n" + "="*80)
        print("5️⃣ 네이버 클라우드 연결 테스트")
        print("="*80)
        
        try:
            import boto3
            
            # 자격증명
            access_key = os.getenv('NAVER_ACCESS_KEY')
            secret_key = os.getenv('NAVER_SECRET_KEY')
            bucket = os.getenv('NAVER_BUCKET_NAME')
            region = os.getenv('NAVER_REGION', 'kr-standard')
            
            # S3 클라이언트 생성
            s3_client = boto3.client(
                's3',
                endpoint_url='https://kr.object.ncloudstorage.com',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # 연결 테스트 (버킷 리스트)
            response = s3_client.list_buckets()
            
            buckets = [b['Name'] for b in response.get('Buckets', [])]
            print(f"✅ 네이버 클라우드 연결 성공")
            print(f"   엔드포인트: https://kr.object.ncloudstorage.com")
            print(f"   접근 가능한 버킷: {', '.join(buckets) if buckets else '(없음)'}")
            
            # 지정된 버킷이 있는지 확인
            if bucket in buckets:
                print(f"✅ Bucket '{bucket}' 접근 가능")
                self.checks['naver_cloud'] = True
                return True
            else:
                print(f"⚠️ Bucket '{bucket}'을 찾을 수 없습니다")
                print(f"   네이버 클라우드 콘솔에서 생성해주세요")
                print(f"   https://console.ncloud.com/object-storage")
                return False
        
    
        except Exception as e:
            print(f"❌ 네이버 클라우드 연결 실패: {e}")
            print("   Access Key, Secret Key 확인하세요")
            return False
        '''
    
    def run_all_checks(self):
        """모든 확인 실행"""
        print("\n" + "🚀 "*40)
        print("Day 1: 환경설정 및 연결 테스트 시작")
        print("🚀 "*40)
        
        # 1. Python 버전
        py_ok = self.check_python_version()
        if not py_ok:
            logger.error("Python 3.10.13 설치 필요")
            return False
        
        # 2. 패키지
        pkg_ok = self.check_packages()
        
        # 3. 환경 변수
        env_ok = self.check_env_variables()
        if not env_ok:
            logger.error("환경 변수 설정 필요")
            return False
        
        # 4. 디렉토리
        dir_ok = self.check_directories()
        
        # 5. 네이버 클라우드
        # ncloud_ok = self.check_naver_cloud()   # ❌ 현재 프로젝트에서는 사용하지 않음 
        
        # 결과
        print("\n" + "="*80)
        print("📊 최종 결과")
        print("="*80)
        
        results = {
            '✅ Python 3.10': py_ok,
            '✅ 필수 패키지': pkg_ok,
            '✅ 환경 변수': env_ok,
            '✅ 디렉토리': dir_ok,
            '✅ 네이버 클라우드': ncloud_ok,
        }
        
        for check, result in results.items():
            status = "완료" if result else "필요"
            mark = "✅" if result else "⚠️"
            print(f"{mark} {check}: {status}")
        
        all_ok = all(results.values())
        
        if all_ok:
            print("\n" + "="*80)
            print("🎉 Day 기본 환경설정 완료!")
            print("="*80)
            print("""
다음 단계:
1. Day 2: 문서 처리 파이프라인 구축
   → PDF, PPT, Word 파일 자동 처리

실행: python setup_document_processor.py
            """)
            return True
        else:
            print("\n" + "="*80)
            print("⚠️ 설정 필요한 항목이 있습니다")
            print("="*80)
            print("""
필수 작업:
1. Python 3.10.13 설치 (필요시)
2. pip install -r requirements.txt
3. .env 파일에 모든 값 입력
4. 네이버 클라우드 버킷 생성
            """)
            return False


def main():
    checker = EnvironmentChecker()
    success = checker.run_all_checks()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
