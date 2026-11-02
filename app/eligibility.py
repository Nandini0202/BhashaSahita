"""Rule-based eligibility engine. The LLM never decides eligibility (see README)."""

OPS = {
    "eq":  lambda a, b: a == b,
    "ne":  lambda a, b: a != b,
    "in":  lambda a, b: a in b,
    "gte": lambda a, b: a >= b,
    "lte": lambda a, b: a <= b,
    "between": lambda a, b: b[0] <= a <= b[1],
}

def check_condition(cond: dict, profile: dict) -> str:
    """Returns 'match', 'no_match' or 'unknown' (missing info is never assumed to match).
    Supports {"any_of": [cond, ...]} groups (match if any matches; no_match only if all fail)."""
    if "any_of" in cond:
        sub = [check_condition(c, profile) for c in cond["any_of"]]
        if "match" in sub: return "match"
        return "no_match" if all(x == "no_match" for x in sub) else "unknown"
    value = profile.get(cond["field"])
    if value is None:
        return "unknown"
    return "match" if OPS[cond["op"]](value, cond["value"]) else "no_match"

def evaluate(scheme: dict, profile: dict) -> dict:
    results = [{"label": c.get("label", c.get("field", "any_of")), "status": check_condition(c, profile)}
               for c in scheme.get("conditions", [])]
    total = len(results)
    matched = sum(r["status"] == "match" for r in results)
    failed = sum(r["status"] == "no_match" for r in results)
    pending = total - matched - failed
    if failed:
        verdict = "not_eligible"
    elif pending:
        verdict = "possibly_eligible"        # needs more info
    else:
        verdict = "meets_listed_conditions"  # still subject to official verification
    return {"scheme_id": scheme["id"], "matched": matched, "total": total,
            "pending": pending, "failed": failed, "verdict": verdict, "conditions": results}
