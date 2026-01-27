# (단락보존 + 키워드 가중치형)
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 1. 단락 중심 구분자 설정
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1200,
    chunk_overlap=200,
    separators=["\n\n", "\n", " ", ""], # 문단 구분 우선
    length_function=len,
)

# 2. 로딩 루프 내 로직 수정
def process_text_with_weight(text, filename):
    # 핵심 약어 가중치 주입
    priority_keywords = "PDT(광역동치료), 사업성평가, 정동회계법인, WACC, FCF"
    header = f"[파일출처: {filename}] [핵심키워드: {priority_keywords}]\n"
    
    # 공백이 많은 표 데이터 구조 보존 (공백 2개 이상을 탭으로 치환)
    clean_text = re.sub(r' {2,}', '\t', text)
    
    # 청킹 실행
    chunks = text_splitter.split_text(clean_text)
    
    # 각 청크 앞에 헤더(키워드) 강제 결합
    weighted_chunks = [header + chunk for chunk in chunks]
    return weighted_chunks
