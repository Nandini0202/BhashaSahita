"""
Metadata Extraction for Government Scheme Documents.
Extracts structured scheme fields:
- scheme_id, name, level (Central / State), state, ministry
- category, subcategory
- beneficiary, age criteria, income ceiling, social category
- benefit type, benefit amount, frequency, repayment
- required documents
- deadlines and application URLs
"""
import re
from typing import Dict, Any, List

def extract_metadata_from_text(text: str, default_metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Extracts structured scheme metadata from document text.
    Blends with default_metadata if provided (e.g. from seed catalogue).
    """
    meta = dict(default_metadata or {})

    # Extract Scheme Name if not present
    if not meta.get("name_en"):
        m_name = re.search(r"(?:Scheme Name|Name of Scheme|Yojana|Title)[:\s]+([^\n\r]+)", text, re.IGNORECASE)
        if m_name:
            meta["name_en"] = m_name.group(1).strip()

    # Extract Level (Central / State)
    if not meta.get("level"):
        if re.search(r"\b(Central\s+Government|Government\s+of\s+India|GoI|National)\b", text, re.IGNORECASE):
            meta["level"] = "Central"
        elif re.search(r"\b(State\s+Government|Govt\s+of\s+Haryana|Govt\s+of\s+Maharashtra|Govt\s+of\s+Punjab)\b", text, re.IGNORECASE):
            meta["level"] = "State"

    # Extract Benefit Amount (e.g., ₹6,000, Rs 50,000, 2 lakh)
    if "max_benefit_amount" not in meta:
        m_amt = re.search(r"(?:₹|Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)\s*(?:lakh|crore)?", text, re.IGNORECASE)
        if m_amt:
            val_str = m_amt.group(1).replace(",", "")
            try:
                val = float(val_str)
                if "lakh" in text[m_amt.start():m_amt.end() + 10].lower():
                    val *= 100000
                meta["max_benefit_amount"] = int(val)
            except ValueError:
                pass

    # Extract required documents mentioned
    doc_keywords = [
        "Aadhaar Card", "Ration Card", "Income Certificate", "Caste Certificate",
        "Residence Certificate / Domicile", "Bank Passbook", "Land Ownership / Jamabandi",
        "Birth Certificate", "BPL Ration Card", "Disability Certificate", "Passport Photo"
    ]
    detected_docs = meta.get("documents", []) or []
    for doc in doc_keywords:
        if re.search(r"\b" + re.escape(doc.split()[0]) + r"\b", text, re.IGNORECASE):
            if doc not in detected_docs:
                detected_docs.append(doc)
    meta["documents"] = detected_docs

    return meta
