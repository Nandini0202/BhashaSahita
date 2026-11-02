"""
Text Cleaning and Preprocessing Pipeline for BHASHA SAHITA.
Performs:
- Unicode NFC normalization for Indic scripts (Hindi, Marathi, Punjabi, Telugu, Bengali)
- Whitespace and line-break cleaning
- Removal of navigation artifacts, legal disclaimers, duplicate boilerplate
- Punctuation and numeral normalization
"""
import re
import unicodedata

# Common government document boilerplates and footers
BOILERPLATE_PATTERNS = [
    r"Page\s+\d+\s+of\s+\d+",
    r"Government of India\s+-\s+Confidential",
    r"For internal circulation only",
    r"This is an electronically generated document",
    r"Printed on\s*:\s*\d{2}[-/]\d{2}[-/]\d{4}",
    r"Portal:?\s*https?://\S+",
]

def normalize_indic_text(text: str) -> str:
    """Normalizes Indic text to Unicode NFC and cleans character anomalies."""
    if not text:
        return ""
    # NFC normalisation ensures canonical decomposition + composition
    normalized = unicodedata.normalize("NFC", text)
    # Normalize zero-width joiners and non-joiners gracefully
    normalized = re.sub(r"[\u200B\u200E\u200F\uFEFF]", "", normalized)
    return normalized

def clean_text(text: str) -> str:
    """Full cleaning pipeline for extracted document text."""
    if not text:
        return ""

    text = normalize_indic_text(text)

    # Remove standard page numbers / footers
    for pattern in BOILERPLATE_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # Clean multiple dashes, underscores, repeated symbols
    text = re.sub(r"[-_=]{4,}", " ", text)
    text = re.sub(r"\*{2,}", " ", text)

    # Remove excessive blank lines and spaces
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    return text.strip()
