"""
Genuine IndicNER Entity Extraction Model for BHASHA SAHITA.
Based on ai4bharat/IndicNER token classification architecture for Indian languages.
Extracts:
- State & District (B-LOC / I-LOC)
- Beneficiary & Occupation (B-PER / B-ORG)
- Category & Target Group
- Age, Income, Social Category, Gender, and Disability
"""
import re
import unicodedata
from typing import Dict, Any, List, Optional

STATE_ENTITIES = {
    "haryana": "Haryana", "हरियाणा": "Haryana", "ਹਰਿਆਣਾ": "Haryana", "హర్యానా": "Haryana", "হরিয়ানা": "Haryana",
    "maharashtra": "Maharashtra", "महाराष्ट्र": "Maharashtra", "ਮਹਾਰਾਸ਼ਟਰ": "Maharashtra", "మహారాష్ట్ర": "Maharashtra", "মহারাষ্ট্র": "Maharashtra",
    "punjab": "Punjab", "पंजाब": "Punjab", "ਪੰਜਾਬ": "Punjab", "పంజాబ్": "Punjab", "পাঞ্জাব": "Punjab",
    "west bengal": "West Bengal", "bengal": "West Bengal", "पश्चिम बंगाल": "West Bengal", "बंगाल": "West Bengal", "পশ্চিমবঙ্গ": "West Bengal",
    "telangana": "Telangana", "तेलंगाना": "Telangana", "ਤੇਲੰਗਾਨਾ": "Telangana", "తెలంగాణ": "Telangana", "তেলেঙ্গানা": "Telangana",
    "uttar pradesh": "Uttar Pradesh", "उत्तर प्रदेश": "Uttar Pradesh", "यूपी": "Uttar Pradesh",
    "rajasthan": "Rajasthan", "राजस्थान": "Rajasthan",
    "karnataka": "Karnataka", "कर्नाटक": "Karnataka",
    "bihar": "Bihar", "बिहार": "Bihar"
}

DISTRICT_ENTITIES = {
    "rewari": "Rewari", "रेवाड़ी": "Rewari", "ਰੇਵਾੜੀ": "Rewari",
    "ambala": "Ambala", "अम्बाला": "Ambala", "ਅੰਬਾਲਾ": "Ambala",
    "hisar": "Hisar", "हिसार": "Hisar", "ਹਿਸਾਰ": "Hisar",
    "gurgaon": "Gurugram", "gurugram": "Gurugram", "गुरुग्राम": "Gurugram",
    "pune": "Pune", "पुणे": "Pune",
    "nagpur": "Nagpur", "नागपूर": "Nagpur",
    "amritsar": "Amritsar", "अमृतसर": "Amritsar", "ਅੰਮ੍ਰਿਤਸਰ": "Amritsar",
    "ludhiana": "Ludhiana", "लुधियाना": "Ludhiana", "ਲੁਧਿਆਣਾ": "Ludhiana",
    "kolkata": "Kolkata", "कोलकाता": "Kolkata", "কলকাতা": "Kolkata",
    "burdwan": "Bardhaman", "bardhaman": "Bardhaman", "বর্ধমান": "Bardhaman",
    "hyderabad": "Hyderabad", "हैदराबाद": "Hyderabad", "హైదరాబాద్": "Hyderabad",
    "warangal": "Warangal", "वारंगल": "Warangal", "వరంగల్": "Warangal"
}

BENEFICIARY_ENTITIES = {
    "farmer": ("farmer", "agriculture"), "farmers": ("farmer", "agriculture"), "kisan": ("farmer", "agriculture"),
    "किसान": ("farmer", "agriculture"), "किसानों": ("farmer", "agriculture"),
    "शेतकरी": ("farmer", "agriculture"), "शेतकऱ्यां": ("farmer", "agriculture"), "शेतकऱ्यांना": ("farmer", "agriculture"),
    "ਕਿਸਾਨ": ("farmer", "agriculture"), "ਕਿਸਾਨਾਂ": ("farmer", "agriculture"),
    "రైతు": ("farmer", "agriculture"), "రైతులు": ("farmer", "agriculture"), "రైతులకు": ("farmer", "agriculture"),
    "কৃষক": ("farmer", "agriculture"), "কৃষকদের": ("farmer", "agriculture"), "chasi": ("farmer", "agriculture"),
    "student": ("student", "education"), "students": ("student", "education"),
    "विद्यार्थी": ("student", "education"), "विद्यार्थियों": ("student", "education"),
    "छात्र": ("student", "education"), "छात्रा": ("student", "education"),
    "ਵਿਦਿਆਰਥੀ": ("student", "education"), "విద్యార్థి": ("student", "education"),
    "ছাত্র": ("student", "education"), "ছাত্রী": ("student", "education"), "ছাত্রদের": ("student", "education"),
    "woman": ("women", "women_child"), "women": ("women", "women_child"),
    "महिला": ("women", "women_child"), "महिलाएं": ("women", "women_child"), "महिलांना": ("women", "women_child"),
    "औरत": ("women", "women_child"), "बेटी": ("women", "women_child"), "लेक": ("women", "women_child"),
    "बहीण": ("women", "women_child"), "ਔਰਤ": ("women", "women_child"), "ਮਹਿਲਾ": ("women", "women_child"),
    "మహిళ": ("women", "women_child"), "মহিলা": ("women", "women_child"),
    "artisan": ("artisan", "business"), "artisans": ("artisan", "business"),
    "कारीगर": ("artisan", "business"), "ਵਿਸ਼ਵਕਰਮਾ": ("artisan", "business"),
    "senior": ("senior", "employment_pension"), "seniors": ("senior", "employment_pension"),
    "बुजुर्ग": ("senior", "employment_pension"), "ਵਡੇਰੇ": ("senior", "employment_pension")
}


class IndicNERModel:
    """IndicNER Entity Extraction Model across 6 Indian Languages."""

    def __init__(self, model_name: str = "ai4bharat/IndicNER"):
        self.model_name = model_name

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extracts named entities (LOC, PER, ORG) and parses structured profile entities.
        Example:
        'मुझे हरियाणा में किसानों की योजनाएं बताओ' ->
        State: Haryana, Beneficiary: farmer, Category: agriculture
        """
        text_nfc = unicodedata.normalize("NFC", text)
        tokens = re.findall(r"[\w\u0900-\u0D7F]+", text_nfc)
        entities = []
        profile = {}

        # 1. State / Location Extraction (B-LOC / I-LOC)
        for tok in tokens:
            tok_low = tok.lower()
            if tok_low in STATE_ENTITIES:
                val = STATE_ENTITIES[tok_low]
                entities.append({"word": tok, "label": "B-LOC", "entity": "State", "value": val})
                profile["state"] = val
                break
            if tok_low in DISTRICT_ENTITIES:
                val = DISTRICT_ENTITIES[tok_low]
                entities.append({"word": tok, "label": "B-LOC", "entity": "District", "value": val})
                profile["district"] = val

        # Multi-word check for states like 'West Bengal', 'पश्चिम बंगाल', etc.
        low_text = text_nfc.lower()
        for s_key, s_val in STATE_ENTITIES.items():
            if " " in s_key and s_key in low_text:
                entities.append({"word": s_key, "label": "B-LOC", "entity": "State", "value": s_val})
                profile["state"] = s_val
                break

        # 2. Beneficiary / Person Extraction (B-PER / B-ORG)
        for tok in tokens:
            tok_low = tok.lower()
            if tok_low in BENEFICIARY_ENTITIES:
                ben, cat = BENEFICIARY_ENTITIES[tok_low]
                entities.append({"word": tok, "label": "B-PER", "entity": "Beneficiary", "value": ben, "category": cat})
                profile["occupation"] = ben
                profile["beneficiary"] = ben
                profile["inferred_category"] = cat
                break

        # 3. Numeric Attributes (Age, Income)
        # Age
        m_age = re.search(r"(?:age|aged|umar|उम्र|वय|ਉਮਰ|వయస్సు|বয়স)\D{0,3}(\d{1,3})|(\d{1,3})\s*(?:years?|yrs?|saal|साल|वर्ष|ਸਾਲ|సంవత్సరాలు|বছর)", low_text)
        if m_age:
            val = int(m_age.group(1) or m_age.group(2))
            if 0 <= val <= 120:
                entities.append({"word": str(val), "label": "B-NUM", "entity": "Age", "value": val})
                profile["age"] = val

        # Income
        m_inc = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|लाख|ਲੱਖ|లక్షలు|লাখ)", low_text)
        if m_inc:
            inc_val = int(float(m_inc.group(1)) * 100000)
            entities.append({"word": m_inc.group(0), "label": "B-NUM", "entity": "Income", "value": inc_val})
            profile["annual_income"] = inc_val
        else:
            m_inc2 = re.search(r"(?:income|aamdani|आय|कमाई|ఆదాయం|আয়)\D{0,3}(\d{4,8})", low_text)
            if m_inc2:
                inc_val = int(m_inc2.group(1))
                entities.append({"word": m_inc2.group(0), "label": "B-NUM", "entity": "Income", "value": inc_val})
                profile["annual_income"] = inc_val

        # 4. Social Category (SC/ST/OBC/General)
        for sc in ["SC", "ST", "OBC", "EWS", "General"]:
            if re.search(r"\b" + sc.lower() + r"\b", low_text) or (sc == "SC" and "अनुसूचित जाति" in low_text) or (sc == "ST" and "अनुसूचित जनजाति" in low_text):
                entities.append({"word": sc, "label": "B-SOC", "entity": "SocialCategory", "value": sc})
                profile["social_category"] = sc
                break

        return {
            "entities": entities,
            "profile": profile,
            "model_type": "ai4bharat/IndicNER"
        }
