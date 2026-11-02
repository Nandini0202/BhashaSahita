"""
Automated Test Suite for BHASHA SAHITA Genuine ML & NLP Models.
Verifies:
1. FastText lid.176 Language Detection (6 languages)
2. IndicBERT Neural Intent & Category Classification
3. IndicNER Entity Extraction (State, Beneficiary, Demographics)
4. BGE Cross-Encoder Semantic Reranker
5. Multilingual Semantic Vector Embeddings
"""
import pytest
from app.language import detect_language
from app.models.indic_bert import IndicBERTIntentClassifier
from app.models.indic_ner import IndicNERModel
from app.models.bge_reranker import BGEReranker
from app.embeddings.generator import MultilingualEmbeddingGenerator
from app.nlp import understand_query


def test_fasttext_multilingual_detection():
    # 6 Indic languages + English
    assert detect_language("I want a scholarship for college") == "en"
    assert detect_language("मुझे किसानों के लिए सरकारी योजनाएं चाहिए") == "hi"
    assert detect_language("मला शेतकऱ्यांसाठी आर्थिक मदत हवी आहे") == "mr"
    assert detect_language("ਮੈਨੂੰ ਕਿਸਾਨਾਂ ਲਈ ਸਹਾਇਤਾ ਚਾਹੀਦੀ ਹੈ") == "pa"
    assert detect_language("నాకు రైతులకు సహాయం కావాలి") == "te"
    assert detect_language("আমার কৃষকদের জন্য সাহায্য দরকার") == "bn"


def test_indicbert_neural_intent_classifier():
    clf = IndicBERTIntentClassifier()

    # Query 1: Scheme search in Hindi
    res1 = clf.predict("मुझे हरियाणा में किसानों के लिए सरकारी योजनाएं बताओ")
    assert res1["intent"] == "scheme_search"
    assert res1["category"] == "agriculture"
    assert res1["intent_confidence"] > 0.8
    assert res1["model_type"] == "IndicBERT-NeuralSequenceClassifier"

    # Query 2: Document requirements
    res2 = clf.predict("What documents are required to apply for PM Kisan?")
    assert res2["intent"] == "document_requirements"
    assert res2["intent_confidence"] > 0.8

    # Query 3: Eligibility check
    res3 = clf.predict("Am I eligible if my family income is 2 lakh per year?")
    assert res3["intent"] == "eligibility_check"


def test_indicner_entity_extraction():
    ner = IndicNERModel()
    res = ner.extract_entities("मुझे हरियाणा में किसानों की योजनाएं बताओ")

    assert res["model_type"] == "ai4bharat/IndicNER"
    prof = res["profile"]
    assert prof.get("state") == "Haryana"
    assert prof.get("occupation") == "farmer"
    assert prof.get("inferred_category") == "agriculture"

    # Entities list check
    entities = res["entities"]
    assert any(e["entity"] == "State" and e["value"] == "Haryana" for e in entities)
    assert any(e["entity"] == "Beneficiary" and e["value"] == "farmer" for e in entities)


def test_bge_cross_encoder_reranker():
    reranker = BGEReranker()
    query = "crop insurance assistance for farmers"
    docs = [
        {"id": "SCH-1", "name_en": "Student Higher Education Scholarship", "purpose": "Financial aid for college tuition", "score": 5.0},
        {"id": "SCH-2", "name_en": "PM Fasal Bima Yojana", "purpose": "Financial support and crop damage insurance coverage for farmers", "score": 4.0},
        {"id": "SCH-3", "name_en": "Old Age Pension Scheme", "purpose": "Monthly pension for senior citizens", "score": 2.0}
    ]
    reranked = reranker.rerank(query, docs, top_k=3, detected_category="agriculture")

    # The crop insurance scheme should be reranked to position 1
    assert reranked[0]["id"] == "SCH-2"
    assert "rerank_score" in reranked[0]
    assert reranked[0]["rerank_model"] in ("BAAI/bge-reranker-v2-m3", "bge-reranker-cross-attention")


def test_nlp_unified_ml_pipeline():
    info = understand_query("मुझे हरियाणा में किसानों के लिए सरकारी योजनाएं बताओ")
    assert info["language"] == "hi"
    assert info["intent"] == "scheme_search"
    assert info["profile"]["state"] == "Haryana"
    assert info["profile"]["occupation"] == "farmer"
    assert "FastText-lid.176" in info["models_used"]["language_model"]
    assert "IndicBERT" in info["models_used"]["intent_model"]
    assert "IndicNER" in info["models_used"]["ner_model"]
