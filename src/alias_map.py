# alias_map.py

# 1. 도메인 전문 용어 사전
alias_map = {
    # [CLEANING]
    "뀀뀀": "", "조": "", "때문": "", "대한": "", "통해": "", 
    "관련": "", "있음": "", "내용": "", "사항": "", "경우": "",

    # [MEDICAL]
    "중입자": "중입자치료", "중입자가속기": "중입자치료", "heavy ion": "중입자치료",
    "가속기": "중입자치료", "탄소이온": "중입자치료", "linac": "선형가속기",
    "pdt": "광역동치료", "피디티": "광역동치료",

    # [HOSPITALITY]
    "hma": "호텔위탁운영계약", "위탁운영": "호텔위탁운영계약",
    "tsa": "기술자문계약", "technical service": "기술자문계약",
    "jv": "공동개발", "조인트벤처": "공동개발",
    "gsa": "총판계약", "판매대행": "총판계약",

    # [FINANCE/BLOCKCHAIN]
    "sto": "토큰증권", "security token": "토큰증권",
    "rwa": "실물자산토큰화", "real world asset": "실물자산토큰화",
    "btc": "가상자산", "비트코인": "가상자산",
    "pf": "프로젝트파이낸싱", "ltv": "담보인정비율",

    # [FEASIBILITY]
    "fs": "사업타당성", "타당성분석": "사업타당성",
    "irr": "내부수익률", "roi": "내부수익률", "이익률": "내부수익률",
    "npv": "순현재가치", "capex": "투자비", "opex": "운영비",
    "연면적": "면적", "gfa": "면적", "평수": "면적", "헤베": "면적"
}

# 2. 음성 발음 오차 보정 사전 (Whisper가 못잡는 것만 추가)
VOICE_CORRECTION = {
    "옆면적": "연면적",
    "이노가": "인허가",
}

def clean_and_refine(query):
    """
    발음 보정 -> 소문자화 -> 도메인 매핑(중복방지) -> 공백 정리 순으로 처리
    """
    # Step 1: 음성 발음 보정
    for wrong, right in VOICE_CORRECTION.items():
        query = query.replace(wrong, right)
        
    query = query.lower().strip()
    
    # Step 2: 도메인 사전 매핑 (긴 단어 우선순위 정렬)
    sorted_keys = sorted(alias_map.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        target_key = key.lower()
        replacement = alias_map[key]
        
        # [중요] 이미 교정된 단어가 문장에 포함되어 있다면 중복 교정 건너뜀
        if replacement and replacement in query:
            continue
            
        if target_key in query:
            query = query.replace(target_key, replacement)
            
    # Step 3: 중복 공백 제거
    return " ".join(query.split())
