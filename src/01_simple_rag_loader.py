#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import hashlib
import fitz  # PyMuPDF
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 라이브러리 로드
import chromadb
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# 1. 환경 설정
TARGET_DIR = Path(r"C:/Users/USER/Downloads/@@@인도네시아PDT암센터FS")
DB_PATH = Path(r"C:/Users/USER/rag/src/data/chroma_db")
COLLECTION_NAME = "indonesia_pdt_docs"
# OpenAI 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # 여기에 키를 넣거나 환경변수 사용
EMBED_MODEL = "text-embedding-3-small" # 가성비와 성능이 가장 좋은 최신 모델

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobustRAGLoaderV2:
    def __init__(self):
        logger.info("🚀 시스템 초기화 (OpenAI Embedding Mode)")
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        
        # ChromaDB 초기화
        self.db_client = chromadb.PersistentClient(path=str(DB_PATH))
        
        # 테스트를 위해 초기화
        try:
            self.db_client.delete_collection(COLLECTION_NAME)
            logger.info(f"🗑️ 기존 컬렉션 '{COLLECTION_NAME}' 초기화 완료")
        except: pass
        
        self.collection = self.db_client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    # ... 기존 import 유지
    def extract_text(self, file_path: Path) -> str:
        """파일별 텍스트 추출 (PyMuPDF 엔진 + 용어 보정)"""
        ext = file_path.suffix.lower()
        text = ""
        try:
            # 1. 파일 확장자별 텍스트 추출
            if ext == '.pdf':
                # PyMuPDF(fitz) 사용 - 한글 추출 능력 우수
                doc = fitz.open(file_path)
                text = " ".join([page.get_text() for page in doc])
                doc.close()
            elif ext == '.docx':
                from docx import Document
                doc = Document(file_path)
                text = "\n".join([p.text for p in doc.paragraphs])
            elif ext == '.pptx':
                from pptx import Presentation
                prs = Presentation(file_path)
                text = " ".join([shape.text for slide in prs.slides for shape in slide.shapes if hasattr(shape, "text")])
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()

            # 2. 한글 인코딩 오류 용어 보정 (Glossary Correction)
            if text:
                corrections = {
                    "싞": "신", "짂": "진", "읶": "인", "핚": "한", 
                    "웎": "원", "상홖": "상환", "읷": "일", "젂": "전",
                    "곾": "관", "첚": "천", "중갂": "중간", "얶": "언",
                    "읻": "인", "싵": "실", "엓": "엑", "짗": "지"
                }
                for wrong, right in corrections.items():
                    text = text.replace(wrong, right)

        except Exception as e:
            logger.error(f"❌ {file_path.name} 추출 실패: {e}")
        
        return text


    def run(self):
        all_files = []
        for root, _, filenames in os.walk(TARGET_DIR):
            for f in filenames:
                p = Path(root) / f
                if p.suffix.lower() in {'.pdf', '.docx', '.pptx', '.txt'}:
                    all_files.append(p)

        logger.info(f"🔍 총 {len(all_files)}개 파일 처리 시작")

        total_chunks = 0
        for idx, file_path in enumerate(all_files, 1):
            raw_text = self.extract_text(file_path)
            if not raw_text: continue

            # 단순 청킹
            chunks = [raw_text[i:i+CHUNK_SIZE] for i in range(0, len(raw_text), CHUNK_SIZE - CHUNK_OVERLAP)]
            
            try:
                # OpenAI 배치 임베딩 (여러 청크를 한 번의 호출로 처리)
                response = self.client.embeddings.create(input=chunks, model=EMBED_MODEL)
                embeddings = [data.embedding for data in response.data]
                # 가짜 임베딩 생성 (모델 크기 1536에 맞춘 랜덤값)
                # import numpy as np
                # embeddings = np.random.rand(len(chunks), 1536).tolist()
    
                # 이제 아래 저장 로직이 정상 작동하며 DB에 숫자가 쌓일 겁니다!
                ids = [hashlib.md5(f"{file_path.name}_{i}".encode()).hexdigest() for i in range(len(chunks))]
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=[{"source": file_path.name} for _ in chunks]
                )
                total_chunks += len(chunks)

                logger.info(f"✅ [{idx}/{len(all_files)}] {file_path.name} ({len(chunks)} Chunks)")
            
            except Exception as e:
                logger.error(f"❌ [{idx}/{len(all_files)}] {file_path.name} 처리 중 에러: {e}")

        logger.info(f"🏁 완료! 총 {total_chunks}개 청크 저장됨.")

if __name__ == "__main__":
    loader = RobustRAGLoaderV2()
    loader.run()
