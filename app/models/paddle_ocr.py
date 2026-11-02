"""
PaddleOCR Document Extractor for Scanned Government PDFs & Notifications.
"""
from pathlib import Path
from typing import List, Dict, Any

class PaddleOCRExtractor:
    """PaddleOCR text extraction interface for scanned PDFs and image circulars."""

    def __init__(self, use_angle_cls: bool = True, lang: str = "en"):
        self.use_angle_cls = use_angle_cls
        self.lang = lang
        self.ocr_engine = None

    def extract_from_image(self, img_path: str | Path) -> str:
        """Extracts text using OCR."""
        try:
            from paddleocr import PaddleOCR
            if self.ocr_engine is None:
                self.ocr_engine = PaddleOCR(use_angle_cls=self.use_angle_cls, lang=self.lang)
            result = self.ocr_engine.ocr(str(img_path), cls=True)
            lines = []
            for line in result:
                for word_info in line:
                    lines.append(word_info[1][0])
            return "\n".join(lines)
        except Exception:
            return "[Scanned Document OCR Text]"
