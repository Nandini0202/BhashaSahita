"""
FastAPI application backend for BHASHA SAHITA.
Exposes:
- GET / : Interactive web application dashboard
- POST /search : Hybrid RAG search across schemes with 10 filter controls & retrieved chunks
- POST /rag/answer : Full document-based RAG answer generation with citations & 3 eligibility indicators
- POST /rag/retrieve : Hybrid chunk retrieval over official government guidelines
- POST /eligibility/evaluate : Deterministic eligibility evaluation with 3 indicators
- GET /rag/stats : Vector store and document ingestion metrics
- GET /schemes : Scheme catalog with filters
- GET /schemes/{id} : Specific scheme details with translations
- POST /explain : Grounded AI scheme explanation (RAG)
- GET /languages : Supported 6 Indic languages
- GET /categories : Category taxonomy and translations
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from .search import search, SCHEMES, SCHEMES_MAP
from .rag import generate_explanation, generate_rag_answer, build_rag_context
from .eligibility import evaluate
from .i18n import get_supported_languages, CATEGORIES, get_translation, localize_scheme
from .vector_store.factory import get_vector_store

app = FastAPI(
    title="BHASHA SAHITA API",
    description="Multilingual RAG-First Government Scheme Platform (6 Languages, 10 Filters, Deterministic Eligibility, Official Citations)",
    version="3.0.0"
)

STATIC_DIR = Path(__file__).parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"


class SearchQuery(BaseModel):
    query: str = ""
    profile: Optional[dict] = None
    state: Optional[str] = None
    category: Optional[str] = None
    level: Optional[str] = None
    district: Optional[str] = None
    beneficiary: Optional[str] = None
    age_group: Optional[str] = None
    family_income: Optional[float] = None
    social_category: Optional[str] = None
    benefit_type: Optional[str] = None
    status: Optional[str] = None
    filters: Optional[dict] = None
    sort_by: str = "relevance"
    lang: Optional[str] = None
    top_k: int = 10
    enable_rag_chunks: bool = True


class RAGAnswerRequest(BaseModel):
    query: str
    profile: Optional[dict] = None
    lang: Optional[str] = None
    filters: Optional[dict] = None
    top_k: int = 5


class RAGRetrieveRequest(BaseModel):
    query: str
    filters: Optional[dict] = None
    top_k: int = 10


class EligibilityRequest(BaseModel):
    scheme_id: str
    profile: dict


class ExplainRequest(BaseModel):
    scheme_id: str
    query: str = ""
    profile: Optional[dict] = None
    lang: str = "en"


@app.get("/", response_class=HTMLResponse)
def serve_ui():
    """Serves the interactive frontend web dashboard."""
    if INDEX_HTML.exists():
        return HTMLResponse(content=INDEX_HTML.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>BHASHA SAHITA API</h1><p>UI file not found.</p>")


@app.post("/search")
def do_search(q: SearchQuery):
    """Executes multilingual hybrid RAG search across schemes with 10 filter controls."""
    return search(
        query=q.query,
        profile=q.profile,
        state=q.state,
        category=q.category,
        level=q.level,
        district=q.district,
        beneficiary=q.beneficiary,
        age_group=q.age_group,
        family_income=q.family_income,
        social_category=q.social_category,
        benefit_type=q.benefit_type,
        status=q.status,
        filters=q.filters,
        sort_by=q.sort_by,
        lang=q.lang,
        top_k=q.top_k,
        enable_rag_chunks=q.enable_rag_chunks
    )


@app.post("/rag/answer")
def rag_answer(req: RAGAnswerRequest):
    """Generates document-grounded multilingual response with citations and deterministic eligibility."""
    return generate_rag_answer(
        query=req.query,
        profile=req.profile,
        lang=req.lang,
        filters=req.filters,
        top_k=req.top_k
    )


@app.post("/rag/retrieve")
def rag_retrieve(req: RAGRetrieveRequest):
    """Retrieves top matching document chunks with page citations from official guidelines."""
    from .embeddings.generator import MultilingualEmbeddingGenerator
    store = get_vector_store()
    emb_gen = MultilingualEmbeddingGenerator()
    query_vec = emb_gen.embed_text(req.query)
    chunks = store.search_hybrid(
        query=req.query,
        query_vector=query_vec,
        top_k=req.top_k,
        filters=req.filters
    )
    return {
        "query": req.query,
        "count": len(chunks),
        "chunks": chunks
    }


@app.post("/eligibility/evaluate")
def evaluate_eligibility(req: EligibilityRequest):
    """Deterministic eligibility check returning 3 separate indicators."""
    scheme = SCHEMES_MAP.get(req.scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail=f"Scheme '{req.scheme_id}' not found")
    return evaluate(scheme, req.profile)


@app.get("/rag/stats")
def rag_stats():
    """Returns vector store and ingestion metrics."""
    store = get_vector_store()
    return {
        "total_chunks": store.count(),
        "total_schemes": len(SCHEMES),
        "vector_dimensions": 256,
        "supported_languages": list(get_supported_languages().keys()),
        "categories_count": len(CATEGORIES)
    }


@app.get("/schemes")
def get_schemes(
    category: Optional[str] = None,
    level: Optional[str] = None,
    state: Optional[str] = None,
    status: Optional[str] = None,
    lang: str = "en"
):
    """Lists schemes with optional filters and localization."""
    filtered = SCHEMES
    if category:
        filtered = [s for s in filtered if s.get("category") == category]
    if level:
        filtered = [s for s in filtered if s.get("level") == level]
    if state:
        filtered = [s for s in filtered if s.get("state") == state]
    if status:
        filtered = [s for s in filtered if s.get("status") == status]
    return [localize_scheme(s, lang) for s in filtered]


@app.get("/schemes/{scheme_id}")
def get_scheme_by_id(scheme_id: str, lang: str = "en"):
    """Fetches details for a specific scheme by ID."""
    s = SCHEMES_MAP.get(scheme_id)
    if not s:
        raise HTTPException(status_code=404, detail=f"Scheme '{scheme_id}' not found")
    localized = localize_scheme(s, lang)
    localized["translation"] = get_translation(scheme_id, lang)
    return localized


@app.post("/explain")
def explain_scheme(req: ExplainRequest):
    """Generates source-grounded explanation for a scheme."""
    return generate_explanation(
        scheme_id=req.scheme_id,
        query=req.query,
        profile=req.profile,
        lang=req.lang
    )


@app.get("/languages")
def supported_languages():
    """Returns supported 6 languages."""
    return get_supported_languages()


@app.get("/categories")
def get_categories():
    """Returns scheme category taxonomy."""
    return CATEGORIES
