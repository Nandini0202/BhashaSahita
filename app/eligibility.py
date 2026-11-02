"""
Deterministic Rule-Based Eligibility Engine for BHASHA SAHITA.
Strict Rule: "The LLM or AI model never decides eligibility."
Only explicit deterministic rules evaluate user qualifications.

Computes 3 Separate Structured Indicators:
1. Eligibility Match: meets_listed_conditions / possibly_eligible / not_eligible
2. Benefit Details: Amount, frequency, benefit type, and repayment status
3. Document Readiness: Available vs missing required documents
"""
import re
from typing import Dict, Any, List, Tuple

OPS = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "in": lambda a, b: (a in b) if isinstance(b, (list, tuple, set, str)) else False,
    "gte": lambda a, b: a >= b,
    "lte": lambda a, b: a <= b,
    "between": lambda a, b: b[0] <= a <= b[1],
}

def check_condition(cond: dict, profile: dict) -> str:
    """
    Returns 'match', 'no_match' or 'unknown'.
    Missing information is NEVER assumed to match.
    Supports {"any_of": [cond, ...]} groups (match if any matches; no_match only if all fail).
    """
    if "any_of" in cond:
        sub = [check_condition(c, profile) for c in cond["any_of"]]
        if "match" in sub:
            return "match"
        return "no_match" if all(x == "no_match" for x in sub) else "unknown"

    value = profile.get(cond["field"])
    if value is None:
        return "unknown"

    try:
        op_func = OPS.get(cond["op"])
        if not op_func:
            return "unknown"
        return "match" if op_func(value, cond["value"]) else "no_match"
    except Exception:
        return "no_match"

def _normalize_doc_name(name: str) -> str:
    """Normalizes document names for flexible matching."""
    s = re.sub(r"[^\w\s]", " ", name.lower())
    s = re.sub(r"\s+", " ", s).strip()
    return s

DOC_SYNONYM_GROUPS = [
    {"aadhaar", "aadhar"},
    {"bank", "passbook", "account"},
    {"land", "jamabandi", "records", "ownership", "khatoni", "7/12"},
    {"ration", "bpl"},
    {"income", "aamdani"},
    {"caste", "jati"},
    {"residence", "domicile", "niwas"},
    {"birth", "janm"},
    {"disability", "divyang", "handicap"}
]

def _docs_match(req: str, user_doc: str) -> bool:
    norm_req = _normalize_doc_name(req)
    norm_u = _normalize_doc_name(user_doc)
    if norm_req in norm_u or norm_u in norm_req:
        return True

    req_words = set(norm_req.split()) - {"card", "certificate", "proof", "copy", "details"}
    u_words = set(norm_u.split()) - {"card", "certificate", "proof", "copy", "details"}

    if req_words and req_words.issubset(u_words):
        return True
    if u_words and u_words.issubset(req_words):
        return True

    # Check synonym groups
    for group in DOC_SYNONYM_GROUPS:
        if any(w in norm_req for w in group) and any(w in norm_u for w in group):
            return True

    return False

def evaluate_document_readiness(required_docs: List[str], user_docs: List[str]) -> Dict[str, Any]:
    """
    Evaluates applicant's document readiness against scheme's required documents.
    Returns available documents, missing documents, readiness score, and status.
    """
    if not required_docs:
        return {
            "required": [],
            "available": list(user_docs or []),
            "missing": [],
            "readiness_percentage": 100.0,
            "status": "ready"
        }

    available = []
    missing = []

    for req in required_docs:
        matched = False
        for raw_u in (user_docs or []):
            if _docs_match(req, raw_u):
                matched = True
                break

        if matched:
            available.append(req)
        else:
            missing.append(req)

    total = len(required_docs)
    pct = round((len(available) / total) * 100.0, 1) if total > 0 else 100.0

    if pct == 100.0:
        status = "ready"
    elif pct > 0:
        status = "partially_ready"
    else:
        status = "needs_documents"

    return {
        "required": required_docs,
        "available": available,
        "missing": missing,
        "readiness_percentage": pct,
        "status": status
    }

def format_benefit_details(scheme: Dict[str, Any]) -> Dict[str, Any]:
    """Structures and formats benefit details."""
    amt = scheme.get("max_benefit_amount", 0)
    freq = scheme.get("benefit_frequency", "one-time")
    btype = scheme.get("benefit_type", "grant")
    repay = scheme.get("repayment_required", False)

    if amt:
        summary = f"{btype.capitalize()} up to ₹{amt:,} ({freq})"
    else:
        summary = f"{btype.capitalize()} ({freq})"

    if repay:
        summary += " [Repayment Required]"
    else:
        summary += " [Non-refundable]"

    return {
        "amount": amt,
        "frequency": freq,
        "benefit_type": btype,
        "repayment_required": repay,
        "summary": summary
    }

def evaluate(scheme: dict, profile: dict) -> dict:
    """
    Evaluates a scheme against user profile deterministically.
    Returns:
    - Top-level backward-compatible keys: matched, total, pending, failed, verdict, conditions
    - Three separate structured indicators:
      1. eligibility_match
      2. benefit_details
      3. document_readiness
    """
    prof = profile or {}
    results = [
        {
            "label": c.get("label", c.get("field", "any_of")),
            "field": c.get("field", "any_of"),
            "status": check_condition(c, prof)
        }
        for c in scheme.get("conditions", [])
    ]

    total = len(results)
    matched = sum(r["status"] == "match" for r in results)
    failed = sum(r["status"] == "no_match" for r in results)
    pending = total - matched - failed

    missing_criteria = [r["label"] for r in results if r["status"] == "unknown"]
    disqualifying_criteria = [r["label"] for r in results if r["status"] == "no_match"]

    if failed:
        verdict = "not_eligible"
    elif pending:
        verdict = "possibly_eligible"  # Needs more profile info
    else:
        verdict = "meets_listed_conditions"

    # Separate Indicator 1: Eligibility Match
    eligibility_match = {
        "verdict": verdict,
        "matched": matched,
        "total": total,
        "pending": pending,
        "failed": failed,
        "conditions": results,
        "missing_criteria": missing_criteria,
        "disqualifying_criteria": disqualifying_criteria
    }

    # Separate Indicator 2: Benefit Details
    benefit_details = format_benefit_details(scheme)

    # Separate Indicator 3: Document Readiness
    user_docs = prof.get("documents") or prof.get("documents_available") or []
    document_readiness = evaluate_document_readiness(
        required_docs=scheme.get("documents", []),
        user_docs=user_docs
    )

    return {
        # Backward compatibility keys
        "scheme_id": scheme.get("id"),
        "matched": matched,
        "total": total,
        "pending": pending,
        "failed": failed,
        "verdict": verdict,
        "conditions": results,
        # 3 Dedicated Structured Indicators
        "eligibility_match": eligibility_match,
        "benefit_details": benefit_details,
        "document_readiness": document_readiness
    }
