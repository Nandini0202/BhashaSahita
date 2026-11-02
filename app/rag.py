"""
RAG & Contextual Explanation Engine for BHASHA SAHITA.
Grounded Q&A over official scheme guidelines with strict source citations.
Rule: "Rules decide eligibility, never the LLM." The LLM or generator explains
the rule evaluation results, documents required, and benefit details.
"""
import os
import json
from pathlib import Path
from .eligibility import evaluate
from .i18n import get_translation, get_category_label

DATA_FILE = Path(__file__).parent.parent / "data" / "schemes_seed.json"
SCHEMES_MAP = {s["id"]: s for s in json.loads(DATA_FILE.read_text(encoding="utf-8"))}

def get_scheme_document_chunks(scheme: dict) -> list[str]:
    """Extracts structured text chunks from scheme metadata and verification notes."""
    sid = scheme["id"]
    name = scheme["name_en"]
    category = scheme["category"]
    purpose = scheme["purpose"]
    btype = scheme.get("benefit_type", "grant")
    bamt = scheme.get("max_benefit_amount", 0)
    freq = scheme.get("benefit_frequency", "")
    repay = "Repayment required" if scheme.get("repayment_required") else "No repayment required (non-refundable)"
    docs = ", ".join(scheme.get("documents", []))
    url = scheme.get("official_url", "")
    pdf_url = scheme.get("official_pdf_url", "")
    notes = scheme.get("verification", {}).get("notes", "")

    chunks = [
        f"Scheme: {name} (ID: {sid}, Level: {scheme.get('level')}, State: {scheme.get('state')}). Ministry: {scheme.get('ministry')}.",
        f"Purpose: {purpose}. Category: {category}.",
        f"Financial Benefit: {btype.capitalize()} of up to Rs {bamt:,} ({freq}). {repay}.",
        f"Required Documents for Application: {docs}.",
        f"Official Portal: {url} | Official Guidelines: {pdf_url}.",
        f"Verification Guidelines & Exclusions: {notes}"
    ]
    return chunks

def generate_explanation(
    scheme_id: str,
    query: str,
    profile: dict | None = None,
    lang: str = "en"
) -> dict:
    """
    Generates a source-grounded explanation for a scheme based on query and user profile.
    Grounded in official scheme facts with citations.
    """
    scheme = SCHEMES_MAP.get(scheme_id)
    if not scheme:
        return {"error": f"Scheme {scheme_id} not found"}

    prof = profile or {}
    elig = evaluate(scheme, prof)
    chunks = get_scheme_document_chunks(scheme)
    tr = get_translation(scheme_id, lang)
    localized_name = tr.get("name", scheme["name_en"])

    sources = [scheme.get("official_url")]
    if scheme.get("official_pdf_url"):
        sources.append(scheme.get("official_pdf_url"))
    for s in scheme.get("verification", {}).get("sources", []):
        if s not in sources:
            sources.append(s)

    # Check if Gemini API key is available
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    llm_generated = False
    explanation_text = ""

    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            prompt = f"""You are the official assistant for BHASHA SAHITA, a government scheme platform.
Explain why scheme '{scheme['name_en']}' ({localized_name}) is relevant to the user query: '{query}'.

GROUND TRUTH RULES & DATA:
{chr(10).join(chunks)}

RULE ENGINE EVALUATION RESULT (DO NOT OVERRIDE):
- Verdict: {elig['verdict']}
- Conditions Matched: {elig['matched']} / {elig['total']}
- Pending/Missing info: {elig['pending']}
- Failed: {elig['failed']}
- Condition Details: {json.dumps(elig['conditions'])}

INSTRUCTIONS:
1. Answer in language code: {lang}.
2. Never claim the user is legally approved or eligible; state that rules show '{elig['verdict']}'.
3. State the financial benefit clearly and document requirements.
4. Cite official URL: {scheme['official_url']}
Keep response concise, empathetic, and factual."""
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            if response and response.text:
                explanation_text = response.text.strip()
                llm_generated = True
        except Exception:
            llm_generated = False

    if not llm_generated:
        # Deterministic grounded explanation template
        verdict_str = {
            "meets_listed_conditions": "You meet the listed eligibility criteria based on provided profile." if lang == "en" else "आप दी गई जानकारी के अनुसार सूचीबद्ध शर्तों को पूरा करते हैं।",
            "possibly_eligible": "You may be eligible, but additional information/documents are pending verification." if lang == "en" else "आप पात्र हो सकते हैं, लेकिन कुछ जानकारियों का सत्यापन बाकी है।",
            "not_eligible": "Based on listed conditions, you do not meet one or more criteria for this scheme." if lang == "en" else "सूचीबद्ध शर्तों के आधार पर, आप इस योजना के मापदंडों को पूरा नहीं करते हैं।"
        }.get(elig["verdict"], elig["verdict"])

        benefit_str = f"Benefit: up to ₹{scheme.get('max_benefit_amount', 0):,} ({scheme.get('benefit_frequency', '')})" if scheme.get('max_benefit_amount') else f"Benefit: {scheme.get('benefit_type')}"
        doc_str = ", ".join(scheme.get("documents", []))

        if lang == "hi":
            explanation_text = (
                f"**{localized_name}** ({scheme['category']}):\n"
                f"{tr.get('simplified_text', scheme['purpose'])}\n\n"
                f"**पात्रता स्थिति:** {verdict_str} ({elig['matched']}/{elig['total']} शर्तें पूरी).\n"
                f"**वित्तीय लाभ:** {benefit_str}.\n"
                f"**आवश्यक दस्तावेज:** {doc_str}.\n"
                f"**आधिकारिक आवेदन पोर्टल:** {scheme['official_url']}"
            )
        elif lang == "mr":
            explanation_text = (
                f"**{localized_name}**:\n"
                f"{tr.get('simplified_text', scheme['purpose'])}\n\n"
                f"**पात्रता स्थिती:** {verdict_str} ({elig['matched']}/{elig['total']} अटी पूर्ण).\n"
                f"**आर्थिक लाभ:** {benefit_str}.\n"
                f"**आवश्यक कागदपत्रे:** {doc_str}.\n"
                f"**अधिकृत पोर्टल:** {scheme['official_url']}"
            )
        else:
            explanation_text = (
                f"**{localized_name}** ({scheme.get('level')} Scheme - {scheme.get('ministry')}):\n"
                f"{scheme['purpose']}\n\n"
                f"**Eligibility Evaluation:** {verdict_str} ({elig['matched']}/{elig['total']} listed conditions matched).\n"
                f"**Financial Benefit:** {benefit_str} ({'Repayment required' if scheme.get('repayment_required') else 'Non-repayable grant'}).\n"
                f"**Required Documents:** {doc_str}.\n"
                f"**Official Application Link:** {scheme['official_url']}"
            )

    return {
        "scheme_id": scheme_id,
        "scheme_name": scheme["name_en"],
        "scheme_name_local": localized_name,
        "language": lang,
        "eligibility": elig,
        "explanation": explanation_text,
        "sources": sources,
        "llm_powered": llm_generated,
        "last_verified": scheme.get("last_verified")
    }
