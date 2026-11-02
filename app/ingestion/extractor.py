"""
Document Extraction Pipeline for BHASHA SAHITA.
Extracts structured text from:
- Official PDF guidelines (using PyMuPDF with page number & heading tracking)
- Scanned documents / images (OCR fallback interface)
- HTML portals & notifications
- Plain text / Markdown circulars
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import pymupdf as fitz
except ImportError:
    try:
        import fitz
    except ImportError:
        fitz = None


class DocumentExtractor:
    """Extracts text and page-level metadata from diverse document formats."""

    def __init__(self, enable_ocr: bool = False):
        self.enable_ocr = enable_ocr

    def extract_from_file(self, file_path: str | Path) -> List[Dict[str, Any]]:
        """
        Extracts content from a file, returning a list of page/section items:
        [{"page_number": int, "text": str, "headings": list[str], "source": str}, ...]
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = path.suffix.lower()
        if ext == ".pdf":
            return self.extract_pdf(path)
        elif ext in (".html", ".htm"):
            return self.extract_html(path)
        elif ext in (".txt", ".md", ".json"):
            return self.extract_text(path)
        else:
            return self.extract_text(path)

    def extract_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Extracts text per page from a PDF with heading recognition."""
        pages_content = []
        if fitz is None:
            # Fallback if fitz is unavailable
            return [{"page_number": 1, "text": pdf_path.read_text(encoding="utf-8", errors="ignore"), "headings": [], "source": str(pdf_path)}]

        try:
            doc = fitz.open(str(pdf_path))
            for page_idx, page in enumerate(doc):
                page_num = page_idx + 1
                text = page.get_text("text")

                # If text is empty and OCR is enabled, attempt OCR fallback
                if not text.strip() and self.enable_ocr:
                    text = self._ocr_fallback(page)

                headings = self._detect_headings(text)
                pages_content.append({
                    "page_number": page_num,
                    "text": text.strip(),
                    "headings": headings,
                    "source": str(pdf_path)
                })
            doc.close()
        except Exception as e:
            # Graceful fallback reading raw text if PDF parsing has an issue
            pages_content = [{
                "page_number": 1,
                "text": f"Error parsing PDF {pdf_path.name}: {str(e)}",
                "headings": [],
                "source": str(pdf_path)
            }]

        return pages_content

    def extract_html(self, html_path: Path) -> List[Dict[str, Any]]:
        """Extracts clean readable text from HTML portal documents."""
        raw_html = html_path.read_text(encoding="utf-8", errors="ignore")
        # Remove script, style, navigation tags
        cleaned = re.sub(r"<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
        # Extract headings before stripping all tags
        headings = re.findall(r"<h[1-4][^>]*>(.*?)</h[1-4]>", cleaned, flags=re.IGNORECASE)
        headings = [re.sub(r"<[^>]+>", "", h).strip() for h in headings if h.strip()]
        # Strip remaining tags
        text = re.sub(r"<[^>]+>", " ", cleaned)
        text = re.sub(r"\s+", " ", text).strip()

        return [{
            "page_number": 1,
            "text": text,
            "headings": headings,
            "source": str(html_path)
        }]

    def extract_text(self, text_path: Path) -> List[Dict[str, Any]]:
        """Extracts text from plain text or markdown files."""
        content = text_path.read_text(encoding="utf-8", errors="ignore")
        headings = [line.strip("# ").strip() for line in content.splitlines() if line.startswith("#")]

        # Split on markdown section separators or form feed if multi-page
        pages = content.split("\x0c") if "\x0c" in content else [content]
        result = []
        for i, p in enumerate(pages):
            result.append({
                "page_number": i + 1,
                "text": p.strip(),
                "headings": headings,
                "source": str(text_path)
            })
        return result

    def _detect_headings(self, text: str) -> List[str]:
        """Identifies heading lines from extracted text."""
        headings = []
        for line in text.splitlines():
            line_str = line.strip()
            if not line_str or len(line_str) > 100:
                continue
            # Look for numbered sections or title-like lines
            if re.match(r"^(Section|Chapter|\d+\.|\d+\)|\b[A-Z\s]{4,}\b)", line_str, flags=re.IGNORECASE):
                headings.append(line_str)
        return headings[:5]

    def _ocr_fallback(self, page) -> str:
        """OCR interface for image-based or scanned PDFs."""
        try:
            # Check if pytesseract is available
            import pytesseract
            from PIL import Image
            import io
            pix = page.get_pixmap()
            img = Image.open(io.BytesIO(pix.tobytes()))
            return pytesseract.image_to_string(img)
        except Exception:
            return "[OCR text extraction unavailable]"
