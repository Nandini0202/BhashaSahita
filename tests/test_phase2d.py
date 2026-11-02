from app.validate import validate, validate_strict
from app.search import SCHEMES, search
from app.eligibility import evaluate
from collections import Counter

def get(i): return next(x for x in SCHEMES if x["id"] == i)

def test_dataset_size_and_coverage():
    assert len(SCHEMES) >= 40
    assert validate(SCHEMES) == [] and validate_strict(SCHEMES) == []
    cats = Counter(s["category"] for s in SCHEMES)
    assert len(cats) == 7 and min(cats.values()) >= 3
    states = {s["state"] for s in SCHEMES if s["level"] == "State"}
    assert {"Haryana", "Maharashtra"} <= states

def test_apy_taxpayer_and_age():
    s = get("CEN-EMP-004")
    assert evaluate(s, {"age": 30, "has_bank_account": True, "is_income_tax_payer": False})["verdict"] == "meets_listed_conditions"
    assert evaluate(s, {"age": 30, "is_income_tax_payer": True})["verdict"] == "not_eligible"
    assert evaluate(s, {"age": 41})["verdict"] == "not_eligible"

def test_sukanya_style_unknowns_stay_pending():
    r = evaluate(get("CEN-BUS-002"), {"age": 30})
    assert r["verdict"] == "possibly_eligible" and r["pending"] == 3

def test_jsy_any_of_state_or_category():
    s = get("CEN-WCW-003")
    base = {"is_pregnant_or_lactating": True, "institutional_delivery": True}
    assert evaluate(s, {**base, "state": "Bihar"})["verdict"] == "meets_listed_conditions"          # low-performing state
    assert evaluate(s, {**base, "state": "Haryana", "is_bpl": False, "social_category": "General"})["verdict"] == "not_eligible"
    assert evaluate(s, {**base, "state": "Haryana", "is_bpl": True})["verdict"] == "meets_listed_conditions"

def test_standup_any_of_woman_or_scst():
    s = get("CEN-BUS-005")
    p = {"age": 30, "has_business_plan": True}
    assert evaluate(s, {**p, "gender": "female"})["verdict"] == "meets_listed_conditions"
    assert evaluate(s, {**p, "gender": "male", "social_category": "General"})["verdict"] == "not_eligible"

def test_lado_lakshmi_income_limit_updated():
    c = next(c for c in get("HR-WCW-001")["conditions"] if c["field"] == "annual_income")
    assert c["value"] == 180000

def test_ujjwala_four_refills_cap():
    s = get("CEN-HOU-002")
    assert s["max_benefit_amount"] == 1200 and s["verification"]["status"] == "partially_verified"

def test_unconfirmed_schemes_not_marked_open():
    for i in ["CEN-BUS-005", "CEN-EDU-002", "MH-WCW-001", "MH-WCW-002", "CEN-EMP-006", "CEN-AGR-005"]:
        assert get(i)["status"] in {"needs_verification", "closed_check_extension"}

def test_new_schemes_searchable():
    def names(q, **k): return [r["name"] for r in search(q, **k)["results"]]
    assert any("Surya Ghar" in n for n in names("rooftop solar subsidy"))
    assert any("Ladki Bahin" in n or "Lek Ladki" in n for n in names("women monthly aid", state="Maharashtra"))
    assert any("Vishwakarma" in n for n in names("artisan loan toolkit"))
