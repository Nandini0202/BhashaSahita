from app.language import detect_language
from app.nlp import detect_categories, extract_profile
from app.eligibility import evaluate
from app.search import search, SCHEMES

def test_language_detection():
    assert detect_language("I need a scholarship for college") == "en"
    assert detect_language("Mujhe scholarship chahiye.") == "hi"
    assert detect_language("मला शेतकऱ्यांसाठी आर्थिक मदत हवी आहे.") == "mr"
    assert detect_language("मुझे किसानों के लिए सहायता चाहिए") == "hi"
    assert detect_language("ਮੈਨੂੰ ਕਿਸਾਨਾਂ ਲਈ ਸਹਾਇਤਾ ਚਾਹੀਦੀ ਹੈ।") == "pa"
    assert detect_language("আমার কৃষকদের জন্য সাহায্য দরকার") == "bn"
    assert detect_language("నాకు రైతులకు సహాయం కావాలి") == "te"

def test_cross_lingual_category():
    assert "education" in detect_categories("Mujhe scholarship chahiye.")
    assert "agriculture" in detect_categories("मला शेतकऱ्यांसाठी आर्थिक मदत हवी आहे.")
    assert "agriculture" in detect_categories("ਮੈਨੂੰ ਕਿਸਾਨਾਂ ਲਈ ਸਹਾਇਤਾ ਚਾਹੀਦੀ ਹੈ।")
    assert "education" in detect_categories("I need a scholarship for college")

def test_profile_extraction():
    p = extract_profile("I am a farmer from Haryana, age 35, income 2 lakh")
    assert p == {"age": 35, "annual_income": 200000, "state": "Haryana", "occupation": "farmer"}

def test_eligibility_unknown_not_assumed():
    s = next(x for x in SCHEMES if x["id"] == "CEN-AGR-001")
    r = evaluate(s, {"occupation": "farmer"})
    assert r["matched"] == 1 and r["pending"] == 2 and r["verdict"] == "possibly_eligible"
    assert evaluate(s, {"occupation": "student"})["verdict"] == "not_eligible"
    r = evaluate(s, {"occupation": "farmer", "owns_land": True, "is_income_tax_payer": False})
    assert r["verdict"] == "meets_listed_conditions"

def test_search_end_to_end():
    r = search("मला शेतकऱ्यांसाठी आर्थिक मदत हवी आहे")
    assert r["language"] == "mr" and r["results"][0]["category"] == "agriculture"
    assert search("Mujhe scholarship chahiye")["results"][0]["category"] == "education"
