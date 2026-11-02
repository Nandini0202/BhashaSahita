"""
FastAPI application backend for BHASHA SAHITA.
Exposes:
- GET / : Interactive web application dashboard
- POST /search : Multilingual search with 10 filter controls & sorting
- GET /schemes : Scheme catalog with filters
- GET /schemes/{id} : Specific scheme details with translations
- POST /explain : Grounded AI scheme explanation (RAG)
- GET /languages : Supported 6 Indic languages
- GET /categories : Category taxonomy and translations
"""
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from .search import search, SCHEMES
from .rag import generate_explanation
from .i18n import get_supported_languages, CATEGORIES, get_translation, localize_scheme

app = FastAPI(
    title="BHASHA SAHITA API",
    description="Multilingual Government Scheme Discovery Platform (6 Languages, 10 Filters, 100 Verified Schemes)",
    version="2.0.0"
)

STATIC_DIR = Path(__file__).parent / "static"
INDEX_HTML = STATIC_DIR / "index.html"

class SearchQuery(BaseModel):
    query: str = ""
    profile: dict | None = None
    state: str | None = None
    category: str | None = None
    level: str | None = None
    district: str | None = None
    beneficiary: str | None = None
    age_group: str | None = None
    family_income: int | float | None = None
    social_category: str | None = None
    benefit_type: str | None = None
    status: str | None = None
    filters: dict | None = None
    sort_by: str = "relevance"
    lang: str | None = None
    top_k: int = 10

class ExplainRequest(BaseModel):
    scheme_id: str
    query: str = ""
    profile: dict | None = None
    lang: str = "en"

@app.get("/", response_class=HTMLResponse)
def serve_ui():
    """Serves the interactive frontend web dashboard."""
    if INDEX_HTML.exists():
        return HTMLResponse(content=INDEX_HTML.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>BHASHA SAHITA API</h1><p>UI file not found.</p>")

@app.post("/search")
def do_search(q: SearchQuery):
    """Executes multilingual search across 100 schemes with 10 filter controls."""
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
        top_k=q.top_k
    )

@app.get("/schemes")
def get_schemes(
    category: str | None = None,
    level: str | None = None,
    state: str | None = None,
    status: str | None = None,
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
    s = next((x for x in SCHEMES if x["id"] == scheme_id), None)
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
