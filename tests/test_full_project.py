"""
Comprehensive Test Suite for BHASHA SAHITA Full Project (Phases 1-7).
Covers:
- 100 schemes dataset size, distribution, strict validation
- 10 search filter controls and sorting
- 6-language multilingual search and localization
- RAG / grounded explanation engine
- SQLite database with schemes and translations tables
- FastAPI endpoint responses and web UI serving
"""
import pytest
from collections import Counter
from app.validate import validate, validate_strict
from app.search import SCHEMES, search
from app.eligibility import evaluate
from app.language import detect_language
from app.nlp import detect_categories, extract_profile
from app.i18n import get_translation, get_supported_languages, get_category_label, localize_scheme
from app.rag import generate_explanation
from db.load_sqlite import load
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_100_schemes_dataset_and_validation():
    assert len(SCHEMES) == 100
    assert validate(SCHEMES) == []
    assert validate_strict(SCHEMES) == []

    cats = Counter(s["category"] for s in SCHEMES)
    assert len(cats) == 7
    assert min(cats.values()) >= 9

    states = {s["state"] for s in SCHEMES if s["level"] == "State"}
    assert {"Haryana", "Maharashtra", "Punjab", "West Bengal", "Telangana"} <= states

    levels = Counter(s["level"] for s in SCHEMES)
    assert levels["Central"] >= 40 and levels["State"] >= 40

def test_ten_filter_controls():
    # 1. Category Filter
    r = search(category="agriculture", top_k=50)
    assert len(r["results"]) > 0
    assert all(x["category"] == "agriculture" for x in r["results"])

    # 2. Level Filter
    r = search(level="Central", top_k=50)
    assert all(x["level"] == "Central" for x in r["results"])

    # 3. State Filter
    r = search(state="West Bengal", top_k=20)
    wb_results = [x for x in r["results"] if x["level"] == "State"]
    assert len(wb_results) > 0
    assert all(x["state"] == "West Bengal" for x in wb_results)

    # 4. Beneficiary Filter
    r = search(beneficiary="student", top_k=20)
    assert any("Scholarship" in x["name"] or "POSHAN" in x["name"] or "Student" in x["name"] for x in r["results"])

    # 5. Age Group Filter
    r = search(age_group="60_plus", top_k=20)
    assert any("Old Age" in x["name"] or "Pension" in x["name"] or "Aasara" in x["name"] for x in r["results"])

    # 6. Family Income Filter
    r = search(family_income=150000, top_k=20)
    assert len(r["results"]) > 0

    # 7. Social Category Filter
    r = search(social_category="SC", top_k=20)
    assert any("SC" in x["name"] or "Post-Matric" in x["name"] for x in r["results"])

    # 8. Benefit Type Filter
    r = search(benefit_type="scholarship", top_k=20)
    assert all(x["benefit_type"] == "scholarship" for x in r["results"])

    # 9. Status Filter
    r = search(status="year_round", top_k=20)
    assert all(x["status"] == "year_round" for x in r["results"])

    # 10. Combined Filters
    r = search(category="education", level="Central", benefit_type="scholarship")
    assert len(r["results"]) > 0
    for x in r["results"]:
        assert x["category"] == "education"
        assert x["level"] == "Central"
        assert x["benefit_type"] == "scholarship"

def test_search_sorting():
    # Sort by benefit amount descending
    r = search(sort_by="benefit", top_k=5)
    amounts = [x["max_benefit_amount"] or 0 for x in r["results"]]
    assert amounts == sorted(amounts, reverse=True)

    # Sort by latest launch year descending
    r = search(sort_by="latest", top_k=5)
    years = [next(s["launch_year"] for s in SCHEMES if s["id"] == x["id"]) for x in r["results"]]
    assert years == sorted(years, reverse=True)

def test_multilingual_search_and_indic_translations():
    # 6 languages query test
    queries = [
        ("I need a scholarship for college", "en", "education"),
        ("मुझे किसानों के लिए सहायता चाहिए", "hi", "agriculture"),
        ("मला महिलांसाठी मदत हवी आहे", "mr", "women_child"),
        ("ਮੈਨੂੰ ਕਿਸਾਨਾਂ ਲਈ ਸਹਾਇਤਾ ਚਾਹੀਦੀ ਹੈ", "pa", "agriculture"),
        ("నాకు వైద్య సహాయం కావాలి", "te", "healthcare"),
        ("আমার কৃষকদের জন্য সাহায্য দরকার", "bn", "agriculture"),
    ]
    for q, expected_lang, expected_cat in queries:
        res = search(q)
        assert res["language"] == expected_lang
        assert res["results"][0]["category"] == expected_cat

def test_i18n_module_and_localization():
    langs = get_supported_languages()
    assert len(langs) == 6
    assert set(langs.keys()) == {"en", "hi", "mr", "pa", "te", "bn"}

    # Localize scheme
    s = next(x for x in SCHEMES if x["id"] == "CEN-AGR-001")
    s_hi = localize_scheme(s, "hi")
    assert s_hi["name_local"] == "पीएम किसान सम्मान निधि"
    assert "₹6,000" in s_hi["purpose_local"]

    s_mr = localize_scheme(s, "mr")
    assert s_mr["name_local"] == "पंतप्रधान किसान सन्मान निधी"

    label = get_category_label("agriculture", "bn")
    assert label == "কৃষি ও কৃষক কল্যাণ"

def test_rag_explanation_engine():
    res = generate_explanation("CEN-AGR-001", "How do I get PM Kisan?", {"occupation": "farmer", "owns_land": True, "is_income_tax_payer": False}, lang="en")
    assert res["scheme_id"] == "CEN-AGR-001"
    assert res["eligibility"]["verdict"] == "meets_listed_conditions"
    assert len(res["sources"]) >= 2
    assert "pmkisan.gov.in" in res["sources"][0]
    assert "PM-KISAN" in res["explanation"]

def test_sqlite_loader_with_translations():
    con = load(":memory:")
    c_schemes = con.execute("SELECT count(*) FROM schemes").fetchone()[0]
    c_trans = con.execute("SELECT count(*) FROM scheme_translations").fetchone()[0]
    assert c_schemes == 100
    assert c_trans == 600

def test_fastapi_endpoints():
    # GET / (UI)
    res = client.get("/")
    assert res.status_code == 200
    assert "BHASHA SAHITA" in res.text

    # POST /search
    res = client.post("/search", json={"query": "scholarship", "category": "education"})
    assert res.status_code == 200
    data = res.json()
    assert data["total_matches"] > 0
    assert "results" in data

    # GET /schemes
    res = client.get("/schemes?category=healthcare")
    assert res.status_code == 200
    assert len(res.json()) >= 9

    # GET /schemes/{id}
    res = client.get("/schemes/CEN-HLT-001?lang=hi")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "CEN-HLT-001"
    assert "translation" in data

    # POST /explain
    res = client.post("/explain", json={"scheme_id": "CEN-HLT-001", "query": "Ayushman card", "lang": "en"})
    assert res.status_code == 200
    assert "PM-JAY" in res.json()["scheme_name"]

    # GET /languages & /categories
    assert client.get("/languages").status_code == 200
    assert client.get("/categories").status_code == 200
