"""
Semantic Chunker for Government Scheme Documents.
Divides document text into meaningful chunks while preserving:
- Scheme context header: [Scheme: <Name> | ID: <ID> | Section: <Heading> | Page: <P>]
- Page numbers
- Section headings
- Filter metadata for vector retrieval
"""
import re
from typing import List, Dict, Any
from .cleaner import clean_text

class DocumentChunker:
    """Chunks documents into semantic sections with sliding windows and context prefixes."""

    def __init__(self, target_chunk_size: int = 350, chunk_overlap: int = 50):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document(
        self,
        pages_content: List[Dict[str, Any]],
        scheme_id: str,
        document_title: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Takes pages from DocumentExtractor and produces structured chunks with context headers.
        """
        chunks = []
        chunk_counter = 1

        for page in pages_content:
            page_num = page.get("page_number", 1)
            raw_text = page.get("text", "")
            cleaned = clean_text(raw_text)
            if not cleaned:
                continue

            headings = page.get("headings", [])
            current_section = headings[0] if headings else "General Information"

            # Split text by paragraphs or sections
            paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]

            current_buffer = []
            current_len = 0

            for para in paragraphs:
                # Check if paragraph itself looks like a section header
                if re.match(r"^(Section|Rule|\d+\.|\d+\))\s+[A-Z]", para):
                    current_section = para.split("\n")[0][:60]

                para_words = para.split()
                if current_len + len(para_words) > self.target_chunk_size and current_buffer:
                    chunk_text = "\n\n".join(current_buffer)
                    chunk_id = f"{scheme_id}_p{page_num}_c{chunk_counter}"

                    # Prepend context header for retrieval grounding
                    context_header = (
                        f"Scheme: {metadata.get('name_en', document_title)} (ID: {scheme_id}) | "
                        f"Level: {metadata.get('level', 'Central')} | "
                        f"State: {metadata.get('state', 'All')} | "
                        f"Category: {metadata.get('category', 'general')} | "
                        f"Section: {current_section} | Page: {page_num}"
                    )
                    full_chunk_text = f"{context_header}\n\n{chunk_text}"

                    chunks.append({
                        "chunk_id": chunk_id,
                        "scheme_id": scheme_id,
                        "document_title": document_title,
                        "section": current_section,
                        "page_number": page_num,
                        "text": full_chunk_text,
                        "raw_text": chunk_text,
                        "metadata": {
                            **metadata,
                            "scheme_id": scheme_id,
                            "section": current_section,
                            "page_number": page_num,
                            "document_title": document_title
                        }
                    })
                    chunk_counter += 1
                    # Overlap: keep last paragraph
                    current_buffer = [para]
                    current_len = len(para_words)
                else:
                    current_buffer.append(para)
                    current_len += len(para_words)

            if current_buffer:
                chunk_text = "\n\n".join(current_buffer)
                chunk_id = f"{scheme_id}_p{page_num}_c{chunk_counter}"
                context_header = (
                    f"Scheme: {metadata.get('name_en', document_title)} (ID: {scheme_id}) | "
                    f"Level: {metadata.get('level', 'Central')} | "
                    f"State: {metadata.get('state', 'All')} | "
                    f"Category: {metadata.get('category', 'general')} | "
                    f"Section: {current_section} | Page: {page_num}"
                )
                full_chunk_text = f"{context_header}\n\n{chunk_text}"

                chunks.append({
                    "chunk_id": chunk_id,
                    "scheme_id": scheme_id,
                    "document_title": document_title,
                    "section": current_section,
                    "page_number": page_num,
                    "text": full_chunk_text,
                    "raw_text": chunk_text,
                    "metadata": {
                        **metadata,
                        "scheme_id": scheme_id,
                        "section": current_section,
                        "page_number": page_num,
                        "document_title": document_title
                    }
                })
                chunk_counter += 1

        return chunks
