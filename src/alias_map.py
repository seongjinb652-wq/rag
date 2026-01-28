# alias_map.py (Cleaning & Expert Version)
alias_map = {
    # [CLEANING] 노이즈 및 의미 없는 단어 제거 (검색어에서 제외)
    "뀀뀀": "", "조": "", "때문": "", "대한": "", "통해": "", 
    "관련": "", "있음": "", "내용": "", "사항": "", "경우": "",

    # [MEDICAL] 중입자 및 첨단 의료 표준화
    "중입자": "중입자치료", "중입자가속기": "중입자치료", "Heavy Ion": "중입자치료",
    "가속기": "중입자치료", "탄소이온": "중입자치료", "LINAC": "선형가속기",
    "사이클로트론": "사이클로트론", "Cyclotron": "사이클로트론",
    "PDT": "광역동치료", "피디티": "광역동치료",

    # [HOSPITALITY] 호텔 및 브랜드 개발
    "HMA": "호텔위탁운영계약", "위탁운영": "호텔위탁운영계약",
    "TSA": "기술자문계약", "Technical Service": "기술자문계약",
    "JV": "공동개발", "조인트벤처": "공동개발",
    "GSA": "총판계약", "판매대행": "총판계약",

    # [FINANCE/BLOCKCHAIN] STO 및 가산자산
    "STO": "토큰증권", "Security Token": "토큰증권",
    "RWA": "실물자산토큰화", "Real World Asset": "실물자산토큰화",
    "BTC": "가상자산", "비트코인": "가상자산",
    "PF": "프로젝트파이낸싱", "LTV": "담보인정비율",

    # [FEASIBILITY] 사업 타당성 핵심 지표
    "FS": "사업타당성", "타당성분석": "사업타당성",
    "IRR": "내부수익률", "ROI": "내부수익률", "이익률": "내부수익률",
    "NPV": "순현재가치", "CAPEX": "투자비", "OPEX": "운영비",
    "연면적": "면적", "GFA": "면적", "평수": "면적", "헤베": "면적"
}

def clean_and_refine(query):
    """
    1. 소문자 변환 
    2. 긴 단어부터 매핑 (중복 치환 방지)
    3. 불필요한 공백 제거
    """
    query = query.lower().strip()
    # 단어 길이가 긴 순서대로 정렬 (예: '중입자가속기'를 '가속기'보다 먼저 처리)
    for key in sorted(alias_map.keys(), key=len, reverse=True):
        if key.lower() in query:
            query = query.replace(key.lower(), alias_map[key])
    return " ".join(query.split()) # 중복 공백 제거
