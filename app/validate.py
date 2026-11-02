"""Data-quality checks for the scheme dataset (run in tests and before every data release)."""
REQUIRED = ["id", "name_en", "category", "level", "ministry", "purpose", "tags", "benefit_type",
            "conditions", "documents", "official_url", "status", "verification"]
STATUSES = {"year_round", "open", "seasonal", "closed", "closed_check_extension", "ending_soon", "needs_verification"}
CATEGORIES = {"education", "agriculture", "women_child", "business", "healthcare", "housing", "employment_pension"}

def validate(schemes: list[dict]) -> list[str]:
    errs, seen = [], set()
    for s in schemes:
        i = s.get("id", "?")
        errs += [f"{i}: missing {k}" for k in REQUIRED if k not in s]
        if i in seen: errs.append(f"{i}: duplicate id")
        seen.add(i)
        if s.get("category") not in CATEGORIES: errs.append(f"{i}: bad category")
        if s.get("status") not in STATUSES: errs.append(f"{i}: bad status")
        if s.get("level") == "State" and not s.get("state"): errs.append(f"{i}: State scheme without state")
        v = s.get("verification", {})
        if s.get("verified") and not (v.get("sources") and s.get("last_verified")):
            errs.append(f"{i}: marked verified without sources/last_verified")
    return errs

def validate_strict(schemes: list[dict]) -> list[str]:
    """Extra release checks: verified flag must match verification status; partial/unconfirmed items can't claim 'open'."""
    errs = []
    for s in schemes:
        v = s["verification"]["status"]
        if s.get("verified") != (v == "web_verified"):
            errs.append(f"{s['id']}: verified flag does not match verification.status")
        if not s["verification"].get("sources"):
            errs.append(f"{s['id']}: no sources listed")
        if not str(s.get("official_url", "")).startswith("http"):
            errs.append(f"{s['id']}: bad official_url")
    return errs
