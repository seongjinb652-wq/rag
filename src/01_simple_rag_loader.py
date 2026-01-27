import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """대규모 처리에 최적화된 문서 처리 엔진"""
    
    def __init__(self, settings):
        self.supported_formats = settings.SUPPORTED_FORMATS
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
        
        # 토크나이저 사전 로드 (대량 처리 시 필수)
        try:
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                'sentence-transformers/xlm-r-base-multilingual-nli-stsb',
                clean_up_tokenization_spaces=True
            )
            logger.info("✅ 토크나이저 로드 완료")
        except Exception as e:
            logger.warning(f"⚠️ 토크나이저 로드 실패 (단순 분할 사용): {e}")
            self.tokenizer = None

    def process_file(self, file_path: Path) -> List[str]:
        """파일 형식에 따른 통합 처리 분기"""
        ext = file_path.suffix.lower()
        try:
            if ext == '.pdf': return self._read_pdf(file_path)
            if ext == '.pptx': return self._read_pptx(file_path)
            if ext in ['.docx', '.doc']: return self._read_docx(file_path)
            if ext == '.txt': return self._read_txt(file_path)
            if ext in ['.png', '.jpg', '.jpeg']: return [self._read_image(file_path)]
        except Exception as e:
            logger.error(f"❌ 읽기 에러 ({file_path.name}): {e}")
        return []

    def _read_pdf(self, path):
        from PyPDF2 import PdfReader
        pages = []
        with open(path, 'rb') as f:
            reader = PdfReader(f)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text and text.strip():
                    pages.append(f"[Page {i+1}] {text}")
        return pages

    def _read_pptx(self, path):
        from pptx import Presentation
        slides = []
        prs = Presentation(path)
        for i, slide in enumerate(prs.slides):
            text = [shape.text for shape in slide.shapes if hasattr(shape, "text") and shape.text.strip()]
            if text: slides.append(f"[Slide {i+1}] " + "\n".join(text))
        return slides

    def _read_docx(self, path):
        from docx import Document
        doc = Document(path)
        return [p.text for p in doc.paragraphs if p.text.strip()]

    def _read_txt(self, path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return [f.read()]

    def _read_image(self, path):
        import pytesseract
        from PIL import Image
        if sys.platform == 'win32':
            pytesseract.pytesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        return pytesseract.image_to_string(Image.open(path), lang='kor+eng')

    def make_chunks(self, text: str, source_name: str) -> List[Dict]:
        """텍스트를 청크로 분할 (안전 모드 포함)"""
        if not text.strip(): return []
        
        chunks = []
        if self.tokenizer:
            tokens = self.tokenizer.encode(text)
            for i in range(0, len(tokens), self.chunk_size - self.chunk_overlap):
                chunk_tokens = tokens[i : i + self.chunk_size]
                chunk_text = self.tokenizer.decode(chunk_tokens, skip_special_tokens=True)
                if chunk_text.strip():
                    chunks.append({"text": chunk_text, "metadata": {"source": source_name, "len": len(chunk_text)}})
        else:
            # 폴백 로직: 글자 수 기준 분할
            for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                chunk_text = text[i : i + self.chunk_size]
                chunks.append({"text": chunk_text, "metadata": {"source": source_name, "len": len(chunk_text)}})
        
        return chunks

    def scan_all_files(self, target_dir: Path) -> List[Path]:
        """수천 개의 파일도 재귀적으로 안전하게 스캔"""
        found_files = []
        for root, _, filenames in os.walk(target_dir):
            for f in filenames:
                p = Path(root) / f
                if p.suffix.lower() in self.supported_formats:
                    found_files.append(p)
        return found_files
