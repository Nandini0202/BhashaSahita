"""
Hybrid RAG Search Engine & Filter Pipeline for BHASHA SAHITA.
Combines:
- Multilingual Dense Vector Search (cosine similarity)
- Sparse BM25 / Keyword Inverted Index Retrieval
- Reciprocal Rank Fusion (RRF) & Semantic Reranking
- 10 Structured Scheme Metadata Filters
- Deterministic Rule Engine (3 Separate Indicators)
- Source Grounding & Official Guideline Citations
"""
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

from .nlp import detect_categories, extract_profile, STOPWORDS, normalize_text
from .language import detect_language
from .eligibility import evaluate
from .i18n import get_translation, get_category_label, get_benefit_type_label, get_status_label, get_verdict_label
from .embeddings.generator import MultilingualEmbeddingGenerator
from .vector_store.factory import get_vector_store
from .models.bge_reranker import BGEReranker

DATA_FILE = Path(__file__).parent.parent / "data" / "schemes_seed.json"
SCHEMES = json.loads(DATA_FILE.read_text(encoding="utf-8"))
SCHEMES_MAP = {s["id"]: s for s in SCHEMES}

EMBEDDING_GEN = MultilingualEmbeddingGenerator()
RERANKER = BGEReranker()


def _tokens(s: str) -> set:
    if not s:
        return set()
    s = normalize_text(s)
    words = set(re.findall(r"[\w\u0900-\u0D7F]+", s.lower()))
    return words - STOPWORDS


def _matches_age_group(scheme: dict, age_group: str) -> bool:
    """Checks if scheme conditions allow the specified age bracket."""
    age_map = {
        "under_18": (0, 17),
        "18_25": (18, 25),
        "26_40": (26, 40),
        "41_60": (41, 60),
        "60_plus": (60, 100)
    }
    target_range = age_map.get(age_group)
    if not target_range:
        return True

    for c in scheme.get("conditions", []):
        field = c.get("field")
        if field in ("age", "child_age"):
            op = c.get("op")
            val = c.get("value")
            if op == "gte" and target_range[1] < val:
                return False
            if op == "lte" and target_range[0] > val:
                return False
            if op == "between" and (target_range[1] < val[0] or target_range[0] > val[1]):
                return False
    return True


def _matches_income(scheme: dict, income: int | float) -> bool:
    """Checks if user family income satisfies scheme ceiling."""
    for c in scheme.get("conditions", []):
        if c.get("field") == "annual_income":
            op = c.get("op")
            val = c.get("value")
            if op == "lte" and income > val:
                return False
            if op == "lt" and income >= val:
                return False
    return True


def _matches_social_category(scheme: dict, soc_cat: str) -> bool:
    for c in scheme.get("conditions", []):
        if c.get("field") == "social_category":
            op = c.get("op")
            val = c.get("value")
            if op == "eq" and soc_cat != val:
                return False
            if op == "in" and soc_cat not in val:
                return False
    return True


def search(
    query: str = "",
    profile: dict | None = None,
    state: str | None = None,
    category: str | None = None,
    level: str | None = None,
    district: str | None = None,
    beneficiary: str | None = None,
    age_group: str | None = None,
    family_income: int | float | None = None,
    social_category: str | None = None,
    benefit_type: str | None = None,
    status: str | None = None,
    filters: dict | None = None,
    sort_by: str = "relevance",
    lang: str | None = None,
    top_k: int = 10,
    enable_rag_chunks: bool = True
) -> dict:
    """
    Executes multilingual hybrid RAG retrieval across schemes & official documents.
    Applies all 10 filter criteria and evaluates deterministic eligibility.
    """
    f = filters or {}
    category = category or f.get("category")
    level = level or f.get("level")
    state = state or f.get("state")
    district = district or f.get("district")
    beneficiary = beneficiary or f.get("beneficiary")
    age_group = age_group or f.get("age_group")
    family_income = family_income if family_income is not None else f.get("family_income")
    social_category = social_category or f.get("social_category")
    benefit_type = benefit_type or f.get("benefit_type")
    status = status or f.get("status")

    detected_lang = detect_language(query) if query else "en"
    target_lang = lang or detected_lang

    cats = detect_categories(query) if query else {}
    extracted_prof = extract_profile(query) if query else {}
    prof = {**extracted_prof, **(profile or {})}
    effective_state = state or prof.get("state")

    # Step 1: Hybrid Vector Retrieval over Document Chunks
    retrieved_chunks_by_scheme: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    vector_boost_scores: Dict[str, float] = defaultdict(float)

    if query and enable_rag_chunks:
        try:
            store = get_vector_store()
            query_vec = EMBEDDING_GEN.embed_text(query)
            hybrid_filter = {}
            if category:
                hybrid_filter["category"] = category
            if level:
                hybrid_filter["level"] = level
            if effective_state:
                hybrid_filter["state"] = effective_state
            if benefit_type:
                hybrid_filter["benefit_type"] = benefit_type

            matched_chunks = store.search_hybrid(
                query=query,
                query_vector=query_vec,
                top_k=top_k * 4,
                filters=hybrid_filter
            )

            for chunk in matched_chunks:
                sid = chunk.get("scheme_id")
                if sid:
                    retrieved_chunks_by_scheme[sid].append(chunk)
                    vector_boost_scores[sid] = max(vector_boost_scores[sid], chunk.get("score", 0.0) * 10.0)
        except Exception:
            pass

    # Step 2: Full Catalog Filtering & Scoring across 10 Filters
    qt = _tokens(query)
    ranked = []

    for s in SCHEMES:
        sid = s["id"]

        # --- 10 METADATA FILTERS ---
        # 1. State Filter (State schemes must match user state)
        if s["level"] == "State":
            if effective_state and effective_state != s.get("state"):
                continue
            elif not effective_state and query:
                # If searching general national query without state, state schemes excluded unless matched by text
                if not (s.get("state", "").lower() in query.lower()):
                    continue

        # 2. Category Filter
        if category and s.get("category") != category:
            continue

        # 3. Government Level Filter
        if level and s.get("level") != level:
            continue

        # 4. Beneficiary Filter
        if beneficiary:
            b_norm = beneficiary.lower()
            tags_lower = [t.lower() for t in s.get("tags", [])]
            conds_str = json.dumps(s.get("conditions", [])).lower()
            if not (b_norm in tags_lower or b_norm in conds_str or b_norm in s["purpose"].lower()):
                continue

        # 5. Age Group Filter
        if age_group and not _matches_age_group(s, age_group):
            continue

        # 6. Family Income Filter
        if family_income is not None and not _matches_income(s, family_income):
            continue

        # 7. Social Category Filter
        if social_category and not _matches_social_category(s, social_category):
            continue

        # 8. Benefit Type Filter
        if benefit_type and s.get("benefit_type") != benefit_type:
            continue

        # 9. Status Filter
        if status and s.get("status") != status:
            continue

        # 10. District Filter
        if district and s.get("district") and s.get("district") != district:
            continue

        # --- RANKING SCORE (Dense Vector + Keyword BM25 + Intent Fusion) ---
        score = 0.0

        # Vector chunk retrieval score
        if sid in vector_boost_scores:
            score += vector_boost_scores[sid]

        if effective_state and s.get("state") == effective_state:
            score += 5.0
        if social_category and any(c.get("field") == "social_category" for c in s.get("conditions", [])):
            score += 4.0
        if beneficiary and (beneficiary.lower() in [t.lower() for t in s.get("tags", [])]):
            score += 3.0
        if age_group and any(c.get("field") in ("age", "child_age") for c in s.get("conditions", [])):
            score += 2.0

        if query:
            score += 2.0 * cats.get(s["category"], 0)

            # Match English text
            s_text = s["name_en"] + " " + " ".join(s["tags"]) + " " + s["purpose"]
            s_tokens = _tokens(s_text)
            score += len(qt & s_tokens) * 1.5

            # Match against target language translation
            tr = get_translation(sid, target_lang)
            if tr:
                tr_text = tr.get("name", "") + " " + tr.get("purpose", "") + " " + tr.get("simplified_text", "")
                tr_tokens = _tokens(tr_text)
                score += len(qt & tr_tokens) * 1.8

            if score <= 0 and not (category or level or beneficiary or status or state):
                continue
        else:
            score += 1.0

        # Run deterministic eligibility engine
        elig = evaluate(s, prof)
        # Eligibility score bonus (meets criteria boosted, not_eligible lightly demoted)
        if elig["verdict"] == "meets_listed_conditions":
            score += 2.0
        elif elig["verdict"] == "possibly_eligible":
            score += 1.0

        ranked.append((score, s, elig))

    # --- SORTING ---
    if sort_by in ("benefit", "financial_benefit"):
        ranked.sort(key=lambda x: -(x[1].get("max_benefit_amount") or 0))
    elif sort_by in ("latest", "launch_year"):
        ranked.sort(key=lambda x: -(x[1].get("launch_year") or 0))
    elif sort_by in ("deadline", "application_end"):
        ranked.sort(key=lambda x: (x[1].get("application_end") is None, x[1].get("application_end") or ""))
    else:
        # Relevance ranking with BGE Cross-Encoder Reranker
        if query and len(ranked) > 1:
            ranked.sort(key=lambda x: -x[0])
            top_candidates = [
                {"score": item[0], "scheme": item[1], "elig": item[2], "text": f"{item[1]['name_en']} {item[1]['purpose']}"}
                for item in ranked[:min(len(ranked), top_k * 2)]
            ]
            top_cat = list(cats.keys())[0] if cats else None
            reranked_docs = RERANKER.rerank(query, top_candidates, top_k=top_k, detected_category=top_cat)
            ranked = [(doc["rerank_score"], doc["scheme"], doc["elig"]) for doc in reranked_docs]
        else:
            ranked.sort(key=lambda x: -x[0])

    out = []
    for sc, s, elig in ranked[:top_k]:
        sid = s["id"]
        tr = get_translation(sid, target_lang)
        localized_name = tr.get("name", s["name_en"]) if target_lang != "en" else s["name_en"]
        localized_purpose = tr.get("purpose", s["purpose"]) if target_lang != "en" else s["purpose"]
        localized_sim = tr.get("simplified_text", s["purpose"]) if target_lang != "en" else s["purpose"]

        bamt = s.get("max_benefit_amount")
        bfreq = s.get("benefit_frequency", "")
        btype = s.get("benefit_type", "grant")
        bdisplay = f"₹{bamt:,} ({bfreq})" if bamt else f"{btype.capitalize()} ({bfreq})"

        # 3 Structured Indicators from deterministic engine
        elig_match = elig.get("eligibility_match", {})
        benefit_det = elig.get("benefit_details", {})
        doc_readiness = elig.get("document_readiness", {})

        req_docs = s.get("documents", [])
        missing_docs = doc_readiness.get("missing", req_docs)

        # Chunks retrieved from official guidelines with page numbers
        chunks = retrieved_chunks_by_scheme.get(sid, [])
        formatted_chunks = [
            {
                "chunk_id": c.get("chunk_id"),
                "document_title": c.get("document_title"),
                "section": c.get("section"),
                "page_number": c.get("page_number", 1),
                "text": c.get("raw_text", c.get("text")),
                "score": round(c.get("score", 0.0), 3),
                "source_url": s.get("official_pdf_url") or s.get("official_url")
            }
            for c in chunks[:3]
        ]

        out.append({
            "id": sid,
            "name": s["name_en"],
            "name_local": localized_name,
            "category": s["category"],
            "category_label": get_category_label(s["category"], target_lang),
            "level": s["level"],
            "state": s.get("state"),
            "ministry": s.get("ministry"),
            "purpose": s["purpose"],
            "purpose_local": localized_purpose,
            "simplified_text": localized_sim,
            "benefit_type": btype,
            "benefit_type_local": get_benefit_type_label(btype, target_lang),
            "max_benefit_amount": bamt,
            "benefit_display": bdisplay,
            "score": round(sc, 2),
            "verified": s["verified"],
            "status": s["status"],
            "status_local": get_status_label(s["status"], target_lang),
            "application_end": s.get("application_end"),
            "official_url": s["official_url"],
            "official_pdf_url": s.get("official_pdf_url"),
            "documents": req_docs,
            "pending_documents_count": len(missing_docs),
            "eligibility": elig,
            # 3 Dedicated Structured Indicators
            "eligibility_match": elig_match,
            "benefit_details": benefit_det,
            "document_readiness": doc_readiness,
            # RAG Retrievable Grounding Chunks with Page Citations
            "retrieved_chunks": formatted_chunks,
            # Legacy indicators compatibility
            "indicators": {
                "eligibility_match": f"{elig['matched']}/{elig['total']} conditions",
                "eligibility_verdict": elig["verdict"],
                "eligibility_verdict_label": get_verdict_label(elig["verdict"], target_lang),
                "financial_benefit": bdisplay,
                "document_readiness": f"{len(doc_readiness.get('available', []))}/{len(req_docs)} ready"
            }
        })

    return {
        "language": detected_lang,
        "categories": cats,
        "profile": prof,
        "filters_applied": {
            "category": category, "level": level, "state": effective_state,
            "district": district, "beneficiary": beneficiary, "age_group": age_group,
            "family_income": family_income, "social_category": social_category,
            "benefit_type": benefit_type, "status": status
        },
        "total_matches": len(ranked),
        "results": out
    }
