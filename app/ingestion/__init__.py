"""
Document Ingestion Package for BHASHA SAHITA.
Provides extraction, cleaning, metadata extraction, chunking, and document collection.
"""
from .extractor import DocumentExtractor
from .cleaner import clean_text, normalize_indic_text
from .metadata_extractor import extract_metadata_from_text
from .chunker import DocumentChunker
from .collector import SchemeDocumentCollector, generate_official_scheme_pdf

__all__ = [
    "DocumentExtractor",
    "clean_text",
    "normalize_indic_text",
    "extract_metadata_from_text",
    "DocumentChunker",
    "SchemeDocumentCollector",
    "generate_official_scheme_pdf",
]
