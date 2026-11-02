from app.validate import validate
from app.search import SCHEMES, search
from app.eligibility import evaluate
from db.load_sqlite import load

def test_dataset_valid():
    assert validate(SCHEMES) == []

def test_pmjay_any_of():
    s = next(x for x in SCHEMES if x["id"] == "CEN-HLT-001")
    assert evaluate(s, {"age": 72})["verdict"] == "meets_listed_conditions"
    assert evaluate(s, {"age": 40, "secc_listed": False})["verdict"] == "not_eligible"
    assert evaluate(s, {"age": 40})["verdict"] == "possibly_eligible"   # SECC status unknown

def test_mgnrega_search_finds_replacement():
    names = [r["name"] for r in search("MGNREGA rural job")["results"]]
    assert any("VB-G RAM G" in n for n in names)

def test_haryana_schemes_only_for_haryana():
    ids = [r["id"] for r in search("women monthly assistance")["results"]]
    assert "HR-WCW-001" not in ids
    r = search("women monthly assistance", state="Haryana")["results"]
    assert any(x["id"] == "HR-WCW-001" for x in r)

def test_sqlite_roundtrip():
    con = load()
    assert con.execute("select count(*) from schemes").fetchone()[0] == len(SCHEMES)

def test_verified_count_and_mudra():
    assert sum(s["verified"] for s in SCHEMES) >= 14
    m = next(x for x in SCHEMES if x["id"] == "CEN-BUS-001")
    assert m["max_benefit_amount"] == 2000000 and m["repayment_required"] is True

def test_pmayg_never_confirmed_without_awaas_list():
    s = next(x for x in SCHEMES if x["id"] == "CEN-HOU-001")
    r = evaluate(s, {"residence": "rural", "has_pucca_house": False, "monthly_household_income": 9000})
    assert r["verdict"] == "possibly_eligible" and r["pending"] == 1

def test_no_unverified_left_and_statuses():
    assert all(s["verification"]["status"] != "unverified" for s in SCHEMES)
    nsp = next(x for x in SCHEMES if x["id"] == "CEN-EDU-001")
    assert nsp["status"] == "closed_check_extension" and nsp["application_end"] == "2026-10-31"

def test_ssy_below_10_and_oas_haryana():
    ssy = next(x for x in SCHEMES if x["id"] == "CEN-WCW-002")
    assert evaluate(ssy, {"child_gender": "female", "child_age": 10})["verdict"] == "not_eligible"
    oas = next(x for x in SCHEMES if x["id"] == "HR-EMP-001")
    assert evaluate(oas, {"age": 65, "annual_income": 250000, "state": "Haryana"})["verdict"] == "meets_listed_conditions"
    assert evaluate(oas, {"age": 65, "annual_income": 400000, "state": "Haryana"})["verdict"] == "not_eligible"

def test_search_returns_status():
    r = search("I need a scholarship for college")["results"][0]
    assert "status" in r and "application_end" in r
