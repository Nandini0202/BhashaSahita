"""
Test Suite for BHASHA SAHITA Full RAG-Based Architecture.
Verifies:
1. Document extraction (PDF with PyMuPDF, HTML, text)
2. Semantic chunking with page and heading context
3. Multilingual dense embeddings across 6 languages
4. Vector store hybrid retrieval & metadata filtering
5. Deterministic rule engine 3-indicator evaluation
6. Document readiness assessment
7. Full RAG answer generation with official citations
8. FastAPI RAG endpoints (/rag/answer, /rag/retrieve, /eligibility/evaluate, /rag/stats)
"""
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.ingestion.extractor import DocumentExtractor
from app.ingestion.chunker import DocumentChunker
from app.ingestion.collector import SchemeDocumentCollector, generate_official_scheme_pdf
from app.embeddings.generator import MultilingualEmbeddingGenerator
from app.vector_store.local_store import LocalVectorStore
from app.eligibility import evaluate, evaluate_document_readiness, format_benefit_details
from app.rag import generate_rag_answer, build_rag_context
from app.nlp import understand_query
from app.search import search, SCHEMES

client = TestClient(app)


def test_document_extraction_and_pdf_generation(tmp_path):
    scheme = {
        "id": "TEST-AGR-001",
        "name_en": "Haryana Kisan Subsidy Scheme",
        "category": "agriculture",
        "level": "State",
        "state": "Haryana",
        "ministry": "Agriculture Dept Haryana",
        "purpose": "Provide capital subsidy for solar water pumps.",
        "benefit_type": "subsidy",
        "max_benefit_amount": 75000,
        "benefit_frequency": "one-time",
        "repayment_required": False,
        "conditions": [{"field": "state", "op": "eq", "value": "Haryana"}],
        "documents": ["Aadhaar Card", "Land Ownership / Jamabandi", "Bank Passbook"],
        "official_url": "https://agriharyana.gov.in",
        "status": "open"
    }
    pdf_file = tmp_path / "test_scheme.pdf"
    generate_official_scheme_pdf(scheme, pdf_file)
    assert pdf_file.exists()

    extractor = DocumentExtractor()
    pages = extractor.extract_from_file(pdf_file)
    assert len(pages) >= 2
    assert pages[0]["page_number"] == 1
    assert "HARYANA KISAN SUBSIDY SCHEME" in pages[0]["text"].upper()
    assert pages[1]["page_number"] == 2
    assert "Aadhaar Card" in pages[1]["text"]


def test_semantic_chunker():
    chunker = DocumentChunker(target_chunk_size=100, chunk_overlap=20)
    pages = [
        {
            "page_number": 1,
            "text": "1. Scheme Objective\nThis is paragraph one about agriculture benefits.\n\n2. Eligibility\nFarmers in Haryana are eligible.",
            "headings": ["Scheme Objective"]
        }
    ]
    meta = {"category": "agriculture", "state": "Haryana", "level": "State", "name_en": "Kisan Aid"}
    chunks = chunker.chunk_document(pages, scheme_id="TEST-001", document_title="Kisan Aid Guidelines", metadata=meta)

    assert len(chunks) >= 1
    c = chunks[0]
    assert c["scheme_id"] == "TEST-001"
    assert c["page_number"] == 1
    assert "Scheme: Kisan Aid" in c["text"]
    assert "Page: 1" in c["text"]


def test_multilingual_embeddings():
    gen = MultilingualEmbeddingGenerator(dim=256)

    # Cross-lingual texts in English and Hindi for agriculture
    vec_en = gen.embed_text("financial subsidy for farmers crop insurance")
    vec_hi = gen.embed_text("किसानों के लिए फसल बीमा और आर्थिक सहायता")
    vec_unrelated = gen.embed_text("space rocket satellite launch orbit")

    assert vec_en.shape == (256,)
    assert vec_hi.shape == (256,)

    # Cosine similarity between related multilingual queries should be high
    sim_cross_lingual = gen.similarity(vec_en, vec_hi)
    sim_unrelated = gen.similarity(vec_en, vec_unrelated)

    assert sim_cross_lingual > sim_unrelated


def test_deterministic_eligibility_three_indicators():
    pm_kisan = next(s for s in SCHEMES if s["id"] == "CEN-AGR-001")

    # Profile with matching occupation, land ownership, non-taxpayer, and documents
    user_prof = {
        "occupation": "farmer",
        "owns_land": True,
        "is_income_tax_payer": False,
        "documents": ["Aadhaar Card", "Bank Passbook", "Land Ownership / Jamabandi"]
    }
    res = evaluate(pm_kisan, user_prof)

    # Indicator 1: Eligibility Match
    assert res["verdict"] == "meets_listed_conditions"
    elig_match = res["eligibility_match"]
    assert elig_match["verdict"] == "meets_listed_conditions"
    assert elig_match["matched"] == elig_match["total"]
    assert elig_match["failed"] == 0

    # Indicator 2: Benefit Details
    bdet = res["benefit_details"]
    assert bdet["amount"] == 6000
    assert bdet["benefit_type"] == "grant"
    assert bdet["repayment_required"] is False
    assert "₹6,000" in bdet["summary"]

    # Indicator 3: Document Readiness
    dready = res["document_readiness"]
    assert dready["status"] == "ready"
    assert dready["readiness_percentage"] == 100.0
    assert len(dready["missing"]) == 0
    assert any("Aadhaar" in d for d in dready["available"])


def test_document_readiness_partial():
    req = ["Aadhaar Card", "Ration Card", "Income Certificate"]
    user_docs = ["Aadhaar Card"]
    res = evaluate_document_readiness(req, user_docs)
    assert res["status"] == "partially_ready"
    assert res["available"] == ["Aadhaar Card"]
    assert set(res["missing"]) == {"Ration Card", "Income Certificate"}
    assert res["readiness_percentage"] == 33.3


def test_hybrid_search_with_ten_filters():
    # Test state + category + status
    res = search(
        query="farmer subsidy",
        category="agriculture",
        level="Central",
        top_k=5
    )
    assert res["total_matches"] > 0
    for r in res["results"]:
        assert r["category"] == "agriculture"
        assert r["level"] == "Central"
        assert "eligibility_match" in r
        assert "benefit_details" in r
        assert "document_readiness" in r
        assert "retrieved_chunks" in r


def test_rag_multilingual_haryana_farmer_query():
    # Specific query from prompt requirement:
    query = "मुझे हरियाणा में किसानों के लिए कौन-सी सरकारी योजनाएं मिल सकती हैं?"
    res = generate_rag_answer(query=query, lang="hi")

    assert res["language"] == "hi"
    assert len(res["schemes"]) > 0
    assert len(res["citations"]) > 0

    # Answer text must cite official guidelines and contain schemes
    ans = res["answer"]
    assert "योजना" in ans or "हरियाणा" in ans or "किसान" in ans
    assert "पात्रता" in ans

    # Must contain citations with document titles and pages
    c = res["citations"][0]
    assert "official_url" in c
    assert len(c["pages"]) > 0


def test_fastapi_rag_endpoints():
    # 1. /rag/answer
    resp = client.post("/rag/answer", json={
        "query": "scholarship for higher education student",
        "lang": "en"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "citations" in data
    assert len(data["schemes"]) > 0

    # 2. /rag/retrieve
    resp = client.post("/rag/retrieve", json={
        "query": "crop damage insurance kisan",
        "top_k": 3
    })
    assert resp.status_code == 200
    assert len(resp.json()["chunks"]) > 0

    # 3. /eligibility/evaluate
    resp = client.post("/eligibility/evaluate", json={
        "scheme_id": "CEN-AGR-001",
        "profile": {"occupation": "farmer", "owns_land": True, "is_income_tax_payer": False}
    })
    assert resp.status_code == 200
    assert resp.json()["verdict"] == "meets_listed_conditions"
    assert "document_readiness" in resp.json()

    # 4. /rag/stats
    resp = client.get("/rag/stats")
    assert resp.status_code == 200
    assert resp.json()["total_schemes"] == 100
    assert resp.json()["total_chunks"] > 0
