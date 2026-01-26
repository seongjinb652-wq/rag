# 배치 스케줄러 개선 사항

## 📋 문제점 분석

### 기존 문제
1. **첫 실행**: 루트에 있는 1개 파일만 처리
2. **두 번째 실행**: 0건 처리 (하위 디렉토리 파일을 발견하지 못함)

### 원인
- `list_objects_v2()` 호출 시 기본 파라미터만 사용
- 하위 디렉토리를 재귀적으로 탐색하지 않음
- 1000개 이상의 파일이 있을 경우 페이지네이션 미처리

---

## ✅ 해결 방법

### 1. 하위 디렉토리 재귀 스캔 추가

#### `scan_files()` 메서드 개선

```python
def scan_files(self) -> List[Dict]:
    """Naver Cloud에서 파일 목록 스캔 + 메타데이터 수집 (재귀적)"""
    
    logger.info("🔍 파일 스캔 시작 (하위 디렉토리 포함)...")
    
    files = []
    continuation_token = None
    
    # 페이지네이션으로 모든 파일 스캔
    while True:
        list_params = {
            'Bucket': Settings.NAVER_BUCKET_NAME,
            'MaxKeys': 1000  # 한 번에 최대 1000개
        }
        
        if continuation_token:
            list_params['ContinuationToken'] = continuation_token
        
        response = self.s3_client.list_objects_v2(**list_params)
        
        # 실제 파일만 추가 (디렉토리 제외)
        if 'Contents' in response:
            for obj in response['Contents']:
                if not obj['Key'].endswith('/'):
                    files.append({
                        'name': obj['Key'].split('/')[-1],  # 파일명
                        'path': obj['Key'],  # 전체 경로
                        'size': obj['Size'],
                        'modified': obj['LastModified'].isoformat()
                    })
        
        # 다음 페이지 확인
        if response.get('IsTruncated', False):
            continuation_token = response.get('NextContinuationToken')
        else:
            break
    
    return files
```

#### 주요 변경사항

1. **페이지네이션 루프**
   - `while True` 루프로 모든 파일 스캔
   - `IsTruncated`와 `NextContinuationToken`으로 다음 페이지 확인

2. **파일 정보 구조 변경**
   ```python
   # 기존
   {'name': 'file1.pdf', 'size': 5120, ...}
   
   # 개선
   {
       'name': 'file1.pdf',        # 파일명만
       'path': 'dir1/dir2/file1.pdf',  # 전체 경로
       'size': 5120,
       'modified': '2025-01-26T14:30:00'
   }
   ```

3. **디렉토리 필터링**
   ```python
   if not obj['Key'].endswith('/'):  # 디렉토리 제외
   ```

4. **진행 상황 로깅**
   ```python
   if len(files) % 100 == 0:
       logger.info(f"   스캔 중... {len(files)}개 파일 발견")
   ```

5. **디렉토리별 통계**
   ```python
   logger.info(f"📁 디렉토리별 파일 분포:")
   for dir_path, count in sorted(dir_counts.items()):
       logger.info(f"   {dir_path}: {count}개")
   ```

---

### 2. 파일 추적 키 변경

#### `classify_files()` 메서드 개선

```python
def classify_files(self, all_files: List[Dict]):
    # 전체 경로를 키로 사용
    cloud_files = {f['path'] for f in all_files}  # 'name' → 'path'
    stored_files = set(self.state['processed_files'].keys())
    
    # 신규 파일 찾기
    for file_info in all_files:
        if file_info['path'] not in self.state['processed_files']:
            new_files.append(file_info)
            logger.info(f"   ✨ 신규: {file_info['path']}")
```

#### 상태 파일 구조 변경

```json
{
  "processed_files": {
    "dir1/dir2/file1.pdf": {          // 전체 경로를 키로 사용
      "modified_time": "2025-01-26T14:30:00",
      "file_hash": "abc123def456",
      "file_size": 5120,
      "chunks": 250,
      "status": "processed"
    }
  }
}
```

---

### 3. 다운로드 경로 개선

```python
def download_files(self, files: List[Dict]) -> List[Path]:
    for file_info in files:
        file_key = file_info['path']  # 전체 경로 사용
        
        # 로컬 파일명 (경로 구분자를 언더스코어로 변경)
        local_path = downloads_dir / file_key.replace('/', '_')
        
        self.s3_client.download_file(
            Settings.NAVER_BUCKET_NAME,
            file_key,  # S3에서는 전체 경로 사용
            str(local_path)
        )
```

---

## 📊 예상 결과

### 첫 번째 실행
```
🔍 파일 스캔 시작 (하위 디렉토리 포함)...
   스캔 중... 100개 파일 발견
   스캔 중... 200개 파일 발견
✅ 스캔 완료: 235개 파일 발견

📁 디렉토리별 파일 분포:
   (루트): 1개
   folder1: 50개
   folder1/subfolder1: 30개
   folder2: 154개

📊 분류 완료: 신규 235개, 수정 0개, 삭제 0개
```

### 두 번째 실행
```
🔍 파일 스캔 시작 (하위 디렉토리 포함)...
✅ 스캔 완료: 235개 파일 발견

📁 디렉토리별 파일 분포:
   (루트): 1개
   folder1: 50개
   folder1/subfolder1: 30개
   folder2: 154개

📊 분류 완료: 신규 0개, 수정 0개, 삭제 0개
처리할 새 파일이나 수정 파일이 없습니다
```

---

## 🎯 개선 효과

1. **완전한 파일 탐색**
   - 루트부터 모든 하위 디렉토리까지 재귀적으로 스캔
   - 디렉토리 깊이 제한 없음

2. **대용량 버킷 지원**
   - 1000개 이상의 파일도 페이지네이션으로 처리
   - 메모리 효율적인 스캔

3. **정확한 파일 추적**
   - 전체 경로를 키로 사용하여 동일 파일명 충돌 방지
   - 디렉토리별 파일 현황 파악 가능

4. **상세한 로깅**
   - 100개 단위 진행 상황 표시
   - 디렉토리별 파일 분포 통계

---

## 🔍 테스트 방법

### 1. 상태 파일 초기화 (선택)
```bash
# 상태 파일 백업
cp batch_state.json batch_state.backup.json

# 상태 파일 삭제 (전체 재처리 테스트)
rm batch_state.json
```

### 2. 배치 실행
```bash
python setup_batch_scheduler.py
```

### 3. 로그 확인
```bash
# 실시간 로그
tail -f logs/batch.log

# 리포트 확인
cat logs/batch_report_*.txt
```

---

## 📝 추가 개선 사항

### 향후 고려사항

1. **삭제 파일 처리**
   - 현재: 감지만 하고 미처리
   - 개선: 벡터 DB에서 해당 청크 제거 기능 추가

2. **증분 처리 최적화**
   - 수정된 파일만 재처리하여 성능 개선

3. **병렬 다운로드**
   - `concurrent.futures`로 동시 다운로드

4. **스마트 해시 비교**
   - 파일 크기 + 수정 시간 조합으로 빠른 변경 감지

---

## 🚀 실행 명령어

```bash
# 배치 실행
python setup_batch_scheduler.py

# 스케줄러 등록 (매월 1일 오전 2시)
# → 별도 스케줄러 스크립트 필요
```
