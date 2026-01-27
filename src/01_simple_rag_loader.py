#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# 주요 라이브러리 (필요 시 설치: pip install chromadb sentence-transformers PyPDF2 python-docx python-pptx)
import chromadb
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation

# 1. 설정 (Settings 클래스 대신 직접 선언하여 단순화)
TARGET_DIR = Path(r"C:/Users/USER/Downloads/@@@인도네시아PDT암센터FS")
DB_PATH = Path(r"C:/Users/USER/rag/src/data/chroma_db")
COLLECTION_NAME = "indonesia_pdt_docs"
EMBED_MODEL_NAME = "snunlp/KR-SBERT-V4-KNOWEE" # 한국어 성능이 우수한 모델 추천
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RobustRAGLoader:
    def __init__(self):
        logger.info("🚀 시스템 초기화 중...")
        # DB 초기화
        self.client = chromadb.PersistentClient(path=str(DB_PATH))
        
        # 테스트를 위해 매번 초기화 (필요 시 이 부분 주석 처리)
        try:
            self.client.delete_collection(COLLECTION_NAME)
            logger.info(f"🗑️ 기존 컬렉션 '{COLLECTION_NAME}' 초기화 완료")
        except: pass
        
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME, 
            metadata={"hnsw:space": "cosine"}
        )
        
        # 모델 로드
        self.model = SentenceTransformer(EMBED_MODEL_NAME)
        logger.info(f"✅ 모델 및 DB 준비 완료 ({EMBED_MODEL_NAME})")

    def extract_text(self, file_path: Path) -> str:
        """파일 형식별 텍스트 추출 (하위 디렉토리 대응)"""
        ext = file_path.suffix.lower()
        text = ""
        try:
            if ext == '.pdf':
                reader = PdfReader(file_path)
                text = " ".join([page.extract_text() for page in reader.pages if page.extract_text()])
            elif ext == '.docx':
                doc = Document(file_path)
                text = " ".join([p.text for p in doc.paragraphs])
            elif ext == '.pptx':
                prs = Presentation(file_path)
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if hasattr(shape, "text"): text += shape.text + " "
            elif ext == '.txt':
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
        except Exception as e:
            logger.error(f"❌ 파일 읽기 실패 ({file_path.name}): {e}")
        return text

    def get_chunks(self, text: str) -> List[str]:
        """텍스트를 고정 크기 청크로 분할"""
        if not text: return []
        chunks = []
        for i in range(0, len(text), CHUNK_SIZE - CHUNK_OVERLAP):
            chunks.append(text[i : i + CHUNK_SIZE])
        return chunks

    def run(self):
        start_time = datetime.now()
        # 1. 파일 스캔 (하위 디렉토리 포함)
        all_files = []
        for root, _, filenames in os.walk(TARGET_DIR):
            for f in filenames:
                p = Path(root) / f
                if p.suffix.lower() in {'.pdf', '.docx', '.pptx', '.txt'}:
                    all_files.append(p)

        logger.info(f"🔍 총 {len(all_files)}개의 파일 스캔 완료. 처리를 시작합니다.")

        total_chunks_count = 0
        
        # 2. 파일별 루프
        for idx, file_path in enumerate(all_files, 1):
            raw_text = self.extract_text(file_path)
            chunks = self.get_chunks(raw_text)
            
            if not chunks:
                logger.warning(f"⚠️ [{idx}/{len(all_files)}] {file_path.name} - 추출된 텍스트 없음")
                continue

            # 3. 배치 임베딩 및 저장 (파일 단위)
            try:
                # 파일 내 모든 청크를 한 번에 임베딩 (속도 최적화)
                embeddings = self.model.encode(chunks).tolist()
                
                # 고유 ID 생성 (파일명 + 청크 순번의 해시)
                ids = [hashlib.md5(f"{file_path.name}_{i}".encode()).hexdigest() for i in range(len(chunks))]
                
                metadatas = [{
                    "source": str(file_path),
                    "filename": file_path.name,
                    "date": datetime.now().isoformat()
                } for _ in chunks]

                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=chunks,
                    metadatas=metadatas
                )
                
                total_chunks_count += len(chunks)
                logger.info(f"✅ [{idx}/{len(all_files)}] {file_path.name} - {len(chunks)}개 청크 저장")

            except Exception as e:
                logger.error(f"❌ [{idx}/{len(all_files)}] 저장 실패: {e}")

        duration = datetime.now() - start_time
        logger.info(f"🏁 전체 처리 완료! 총 {total_chunks_count}개 청크 저장 (소요시간: {duration})")

if __name__ == "__main__":
    loader = RobustRAGLoader()
    loader.run()
