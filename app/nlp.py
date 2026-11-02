"""
Multilingual Query Understanding & Profile Extraction for BHASHA SAHITA.
Supports English, Hindi, Marathi, Punjabi, Telugu, and Bengali with Unicode NFC normalization.
Identifies:
- Language
- Intent & 7 Scheme Categories
- Beneficiary & Occupation
- State & District
- Demographics: Age, Income, Gender, Social Category, Residence, Disability
- Available Documents Mentioned
"""
import re
import unicodedata
from typing import Dict, Any, List, Optional
from .language import detect_language

CATEGORY_LEXICON = {
    "education": [
        "scholarship", "student", "college", "school", "education loan", "fellowship", "chhatravritti",
        "tuition", "study", "fee", "degree", "post-matric", "pre-matric", "padhai",
        # Hindi / Marathi
        "छात्रवृत्ति", "विद्यार्थी", "शिष्यवृत्ती", "शिक्षण", "कॉलेज", "शाळा", "महाविद्यालय", "अभ्यास",
        # Punjabi
        "ਵਜ਼ੀਫ਼ਾ", "ਵਜੀਫਾ", "ਵਿਦਿਆਰਥੀ", "ਸਿੱਖਿਆ", "ਪੜ੍ਹਾਈ", "ਸਕੂਲ",
        # Telugu
        "ఉపకార", "ఉపకార వేతనం", "విద్యార్థి", "విద్య", "చదువు", "పాఠశాల",
        # Bengali
        "বৃত্তি", "ছাত্র", "ছাত্রী", "শিক্ষা", "পড়াশোনা", "বিদ্যালয়", "স্কুল"
    ],
    "agriculture": [
        "farmer", "kisan", "crop", "agri", "kheti", "fertilizer", "seed", "tractor", "farm", "fasal",
        # Hindi / Marathi
        "किसान", "खेती", "फसल", "शेतकरी", "शेतकऱ्य", "शेती", "पीक", "कृषि", "बैल", "गोठा", "तळे",
        # Punjabi
        "ਕਿਸਾਨ", "ਖੇਤੀ", "ਫ਼ਸਲ", "ਬੀਜ", "ਖਾਦ", "ਜ਼ਮੀਨ",
        # Telugu
        "రైతు", "వ్యవసాయ", "పంట", "విత్తనాలు", "భూమి", "సాగు",
        # Bengali
        "কৃষক", "কৃষি", "ফসল", "চাষ", "জমি", "বীজ"
    ],
    "women_child": [
        "maternity", "pregnant", "girl child", "women", "woman", "mahila", "beti", "girl", "daughter",
        "marriage grant", "widow", "mother", "infant", "nutrition",
        # Hindi / Marathi
        "गर्भवती", "महिला", "बेटी", "लेक", "गरोदर", "स्त्री", "कन्या", "माता", "बालक", "विवाह", "शादी", "बहीण",
        # Punjabi
        "ਔਰਤ", "ਮਹਿਲਾ", "ਧੀ", "ਕੁੜੀ", "ਵਿਆਹ", "ਸ਼ਗਨ", "ਗਰਭਵਤੀ",
        # Telugu
        "మహిళ", "గర్భిణి", "ఆడపిల్ల", "పెళ్లి", "వివాహం", "తల్లి",
        # Bengali
        "মহিলা", "কন্যা", "মেয়ে", "গর্ভবতী", "বিবাহ", "বিয়ে", "মা"
    ],
    "business": [
        "business", "msme", "startup", "mudra", "self employ", "loan", "shop", "vendor", "artisan",
        "trade", "enterprise", "industry", "khadi", "handicraft",
        # Hindi / Marathi
        "व्यवसाय", "उद्योग", "व्यापार", "दुकान", "स्वरोजगार", "मुद्रा", "कर्ज", "शिल्पी", "कारीगर", "लघु उद्योग",
        # Punjabi
        "ਕਾਰੋਬਾਰ", "ਵਪਾਰ", "ਉੱਦਮ", "ਦੁਕਾਨ", "ਕਰਜ਼ਾ",
        # Telugu
        "వ్యాపార", "పరిశ్రమ", "రుణం", "స్వయం ఉపాధి", "దుకాణం",
        # Bengali
        "ব্যবসা", "উদ্যোগ", "শিল্প", "দোকান", "ঋণ", "স্বনির্ভর"
    ],
    "healthcare": [
        "health", "hospital", "insurance", "treatment", "medical", "doctor", "illness", "medicine",
        "dialysis", "ayushman", "cashless", "surgery",
        # Hindi / Marathi
        "स्वास्थ्य", "इलाज", "आरोग्य", "अस्पताल", "दवा", "दवाखाना", "बीमारी", "विमा", "रुग्णालय", "उपचार",
        # Punjabi
        "ਸਿਹਤ", "ਹਸਪਤਾਲ", "ਇਲਾਜ", "ਦਵਾਈ", "ਬੀਮਾ",
        # Telugu
        "ఆరోగ్య", "ఆరోగ్యం", "వైద్య", "వైద్యం", "ఆసుపత్రి", "చికిత్స", "మందులు", "భీమా",
        # Bengali
        "স্বাস্থ্য", "চিকিৎসা", "হাসপাতাল", "ওষুধ", "অসুখ", "বীমা"
    ],
    "housing": [
        "house", "housing", "toilet", "sanitation", "awas", "roof", "electricity", "tap water", "solar",
        "surya ghar", "shelter", "plot", "latrine",
        # Hindi / Marathi
        "मकान", "आवास", "घरकुल", "घर", "शौचालय", "नल", "बिजली", "सोलर", "सौर", "जागा",
        # Punjabi
        "ਮਕਾਨ", "ਆਵਾਸ", "ਘਰ", "ਟਾਇਲਟ", "ਬਿਜਲੀ", "ਪਾਣੀ",
        # Telugu
        "ఇల్లు", "గృహ", "మరుగుదొడ్డి", "విద్యుత్", "నీరు", "సౌర",
        # Bengali
        "বাড়ি", "আবাস", "শৌচালয়", "বিদ্যুৎ", "জল", "ঘর"
    ],
    "employment_pension": [
        "pension", "job", "employment", "skill", "training", "old age", "disability", "unemployment",
        "apprentice", "wage", "stipend", "worker", "livelihood",
        # Hindi / Marathi
        "रोजगार", "पेंशन", "कौशल", "निवृत्ती", "नौकरी", "प्रशिक्षण", "वृद्धावस्था", "दिव्यांग", "मजदूरी", "बेरोजगार",
        # Punjabi
        "ਪੈਨਸ਼ਨ", "ਰੁਜ਼ਗਾਰ", "ਨੌਕਰੀ", "ਹੁਨਰ", "ਬੁਢਾਪਾ", "ਅਪਾਹਜ",
        # Telugu
        "పింఛన్", "ఉపాధి", "ఉద్యోగం", "నైపుణ్యం", "వృద్ధాప్య", "దివ్యాంగ",
        # Bengali
        "পেনশন", "কর্মসংস্থান", "চাকরি", "দক্ষতা", "বার্ধক্য", "প্রতিবন্ধী"
    ]
}

STATES = {
    "haryana": "Haryana", "हरियाणा": "Haryana", "ਹਰਿਆਣਾ": "Haryana", "హర్యానా": "Haryana", "হরিয়ানা": "Haryana",
    "maharashtra": "Maharashtra", "महाराष्ट्र": "Maharashtra", "ਮਹਾਰਾਸ਼ਟਰ": "Maharashtra", "మహారాష్ట్ర": "Maharashtra", "মহারাষ্ট্র": "Maharashtra",
    "punjab": "Punjab", "पंजाब": "Punjab", "ਪੰਜਾਬ": "Punjab", "పంజాబ్": "Punjab", "পাঞ্জাব": "Punjab",
    "west bengal": "West Bengal", "bengal": "West Bengal", "पश्चिम बंगाल": "West Bengal", "बंगाल": "West Bengal",
    "ਪੱਛਮੀ ਬੰਗਾਲ": "West Bengal", "పశ్చిమ బెంగాల్": "West Bengal", "পশ্চিমবঙ্গ": "West Bengal", "বাংলা": "West Bengal",
    "telangana": "Telangana", "तेलंगाना": "Telangana", "ਤੇਲੰਗਾਨਾ": "Telangana", "తెలంగాణ": "Telangana", "তেলেঙ্গানা": "Telangana",
    "uttar pradesh": "Uttar Pradesh", "उत्तर प्रदेश": "Uttar Pradesh", "यूपी": "Uttar Pradesh", "ਉੱਤਰ ਪ੍ਰਦੇਸ਼": "Uttar Pradesh", "ఉత్తర ప్రదేశ్": "Uttar Pradesh", "উত্তর প্রদেশ": "Uttar Pradesh",
    "rajasthan": "Rajasthan", "राजस्थान": "Rajasthan", "ਰਾਜਸਥਾਨ": "Rajasthan", "రాజస్థాన్": "Rajasthan", "রাজস্থান": "Rajasthan",
    "karnataka": "Karnataka", "कर्नाटक": "Karnataka", "ਕਰਨਾਟਕ": "Karnataka", "కర్ణాటక": "Karnataka", "কর্ণাটক": "Karnataka",
    "bihar": "Bihar", "बिहार": "Bihar", "ਬਿਹਾਰ": "Bihar", "బీహార్": "Bihar", "বিহার": "Bihar"
}

DISTRICTS = {
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

OCCUPATION = {
    "farmer": "farmer", "kisan": "farmer", "किसान": "farmer", "शेतकरी": "farmer", "ਕਿਸਾਨ": "farmer", "రైతు": "farmer", "কৃষক": "farmer", "krishak": "farmer", "chasi": "farmer",
    "student": "student", "विद्यार्थी": "student", "छात्र": "student", "छात्रा": "student", "ਵਿਦਿਆਰਥੀ": "student", "విద్యార్థి": "student", "ছাত্র": "student", "ছাত্রী": "student",
    "artisan": "artisan", "कारीगर": "artisan", "दस्तकार": "artisan", "ਵਿਸ਼ਵਕਰਮਾ": "artisan", "చేతివృత్తి": "artisan", "কারিগর": "artisan",
    "street_vendor": "street_vendor", "vendor": "street_vendor", "रेहड़ी": "street_vendor", "पटरी": "street_vendor", "फेरीवाला": "street_vendor"
}

GENDER = {
    "female": ["female", "woman", "women", "girl", "lady", "mahila", "aurat", "beti", "dhee",
               "महिला", "औरत", "लड़की", "बेटी", "स्त्री", "लेक", "बहीण", "माता",
               "ਔਰਤ", "ਮਹਿਲਾ", "ਧੀ", "ਕੁੜੀ", "ਮਹਿਲਾਵਾਂ",
               "మహిళ", "ఆడపిల్ల", "స్త్రీ",
               "মহিলা", "মেয়ে", "নারী"],
    "male": ["male", "man", "men", "boy", "purush", "aadmi", "ladka",
             "पुरुष", "आदमी", "लड़का", "बेटा",
             "ਮਰਦ", "ਆਦਮੀ", "ਮੁੰਡਾ",
             "పురుషుడు", "అబ్బాయి",
             "পুরুষ", "ছেলে"]
}

SOCIAL_CATEGORIES = {
    "SC": ["sc", "scheduled caste", "अनुसूचित जाति", "दलित", "ਐੱਸ ਸੀ", "షెడ్యూల్డ్ కులం", "তফসিলি জাতি"],
    "ST": ["st", "scheduled tribe", "अनुसूचित जनजाति", "आदिवासी", "ਐੱਸ ਟੀ", "షెడ్యూల్డ్ తెగ", "তফসিলি उपজাতি"],
    "OBC": ["obc", "other backward class", "पिछड़ा वर्ग", "अन्य पिछड़ा वर्ग", "मागासवर्गीय", "ਓ ਬੀ ਸੀ", "వెనుకబడిన తరగతి", "অনগ্রসর শ্রেণি"],
    "EWS": ["ews", "economically weaker section", "आर्थिक रूप से कमजोर", "ఆర్థికంగా బలహీన"],
    "General": ["general", "सामान्य", "ਜਨਰਲ", "జనరల్", "সাধারণ"]
}

DOCUMENT_PATTERNS = {
    "Aadhaar Card": ["aadhaar", "आधार", "ਆਧਾਰ", "ఆధార్", "আধার"],
    "Ration Card": ["ration card", "राशन कार्ड", "रेशन कार्ड", "ਰਾਸ਼ਨ ਕਾਰਡ", "రేషన్ కార్డు", "রেশন কার্ড"],
    "Income Certificate": ["income cert", "आय प्रमाण", "उत्पन्न दाखला", "ਆਮਦਨ ਸਰਟੀਫਿਕੇਟ", "ఆదాయ ధృవీకరణ", "আয় সার্টিফিকেট"],
    "Caste Certificate": ["caste cert", "जाति प्रमाण", "जातीचा दाखला", "ਜਾਤੀ ਸਰਟੀਫਿਕੇਟ", "కుల ధృవీకరణ", "জাতি সার্টিফিকেট"],
    "Bank Passbook": ["bank passbook", "बैंक खाता", "पासबुक", "ਬੈਂਕ ਪਾਸਬੁੱਕ", "బ్యాంక్ పాస్‌బుక్", "ব্যাঙ্ক পাসবই"],
    "Land Ownership / Jamabandi": ["land record", "jamabandi", "7/12", "सातबारा", "जमीन", "భూమి రికార్డు", "খতিয়ান"]
}

STOPWORDS = {
    # English
    "a", "an", "the", "in", "on", "of", "for", "to", "at", "by", "from", "with", "is", "are", "i", "need", "want", "help",
    # Hindi
    "मुझे", "चाहिए", "है", "हैं", "के", "लिए", "और", "क्या", "मेरा", "मेरी", "मेरे", "नहीं", "हूँ", "में", "से", "को", "पर", "का", "की", "योजना",
    # Marathi
    "मला", "हवी", "हवे", "आहे", "आहेत", "साठी", "आणि", "काय", "माझ", "माझे", "माझी", "नाही", "मध्ये", "वर", "कडून", "योजना",
    # Punjabi
    "ਮੈਨੂੰ", "ਚਾਹੀਦੀ", "ਚਾਹੀਦਾ", "ਹੈ", "ਹਨ", "ਲਈ", "ਅਤੇ", "ਕੀ", "ਮੇਰਾ", "ਮੇਰੀ", "ਨਹੀਂ", "ਵਿੱਚ", "ਤੋਂ", "ਤੇ", "ਯੋਜਨਾ",
    # Telugu
    "నాకు", "కావాలి", "ఉంది", "మరియు", "ఏమిటి", "నా", "కాదు", "లో", "నుండి", "కోసం", "పథకం",
    # Bengali
    "আমার", "দরকার", "চাই", "আছে", "এবং", "কি", "জন্য", "না", "মধ্যে", "থেকে", "উপর", "প্রকল্প", "যোজনা"
}

def normalize_text(text: str) -> str:
    """NFC normalization and clean spaces."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    return text.strip()

def detect_categories(text: str) -> dict:
    """Calculates category scores based on multilingual lexicon match."""
    t = normalize_text(text).lower()
    scores = {}
    for c, terms in CATEGORY_LEXICON.items():
        score = 0
        for term in terms:
            term_nfc = unicodedata.normalize("NFC", term).lower()
            if term_nfc in t:
                score += 1
        if score > 0:
            scores[c] = score
    return {c: s for c, s in sorted(scores.items(), key=lambda x: -x[1])}

def extract_profile(text: str) -> dict:
    """Extracts demographic entities and profile attributes from user query."""
    t = normalize_text(text).lower()
    p = {}

    # 1. Age extraction across languages
    m = re.search(r"(?:age|aged|umar|उम्र|वय|ਉਮਰ|వయస్సు|বয়স)\D{0,3}(\d{1,3})|(\d{1,3})\s*(?:years?|yrs?|saal|साल|वर्ष|ਸਾਲ|సంవత్సరాలు|বছর)", t)
    if m:
        val = int(m.group(1) or m.group(2))
        if 0 <= val <= 120:
            p["age"] = val

    # 2. Income extraction (Lakhs, thousands, k)
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:lakh|lac|लाख|ਲੱਖ|లక్షలు|লাখ)", t)
    if m:
        p["annual_income"] = int(float(m.group(1)) * 100000)
    else:
        m2 = re.search(r"(?:income|aamdani|kamai|आय|कमाई|வருமானம்|ఆదాయం|আয়)\D{0,3}(\d{4,8})", t)
        if m2:
            p["annual_income"] = int(m2.group(1))
        else:
            m3 = re.search(r"(\d{2,3})\s*(?:k|hazar|हजार|ਹਜ਼ਾਰ|వేలు|হাজার)", t)
            if m3:
                p["annual_income"] = int(float(m3.group(1)) * 1000)

    # 3. State extraction
    for k, v in STATES.items():
        k_nfc = unicodedata.normalize("NFC", k).lower()
        if k_nfc in t:
            p["state"] = v
            break

    # 3b. District extraction
    for k, v in DISTRICTS.items():
        k_nfc = unicodedata.normalize("NFC", k).lower()
        if k_nfc in t:
            p["district"] = v
            break

    # 4. Occupation extraction
    for k, v in OCCUPATION.items():
        k_nfc = unicodedata.normalize("NFC", k).lower()
        if k_nfc in t:
            p["occupation"] = v
            break

    # 5. Gender extraction
    for g, terms in GENDER.items():
        for term in terms:
            term_nfc = unicodedata.normalize("NFC", term).lower()
            if re.search(r"\b" + re.escape(term_nfc) + r"\b", t) or term_nfc in t:
                p["gender"] = g
                break
        if "gender" in p:
            break

    # 6. Social category extraction
    for cat, terms in SOCIAL_CATEGORIES.items():
        for term in terms:
            term_nfc = unicodedata.normalize("NFC", term).lower()
            if term_nfc in t:
                p["social_category"] = cat
                break
        if "social_category" in p:
            break

    # 7. Rural / Urban residence
    if any(w in t for w in ["rural", "village", "gaon", "gramin", "ग्रामीण", "गांधी", "ਪੇਂਡੂ", "గ్రామీణ", "গ্রামীণ"]):
        p["residence"] = "rural"
    elif any(w in t for w in ["urban", "city", "shahar", "shehari", "शहरी", "शहर", "ਸ਼ਹਿਰੀ", "పట్టణ", "শহুরে"]):
        p["residence"] = "urban"

    # 8. Disability flag
    if any(w in t for w in ["disab", "divyang", "viklang", "handicap", "दिव्यांग", "अपंग", "ਵਿਕਲਾਂਗ", "దివ్యాంగులు", "প্রতিবন্ধী"]):
        p["has_disability"] = True

    # 9. Available documents mentioned
    docs_found = []
    for doc_name, keywords in DOCUMENT_PATTERNS.items():
        for kw in keywords:
            if kw.lower() in t:
                docs_found.append(doc_name)
                break
    if docs_found:
        p["documents_available"] = docs_found

    return p

def understand_query(query: str, lang: Optional[str] = None) -> Dict[str, Any]:
    """
    Full query understanding pipeline:
    - Language detection
    - Category & intent detection
    - Profile / entity extraction (state, district, occupation, age, income, etc.)
    """
    detected_lang = lang or detect_language(query)
    categories = detect_categories(query)
    profile = extract_profile(query)
    primary_category = list(categories.keys())[0] if categories else None

    # Determine intent description
    intent_parts = []
    if profile.get("state"):
        intent_parts.append(f"State: {profile['state']}")
    if profile.get("district"):
        intent_parts.append(f"District: {profile['district']}")
    if profile.get("occupation"):
        intent_parts.append(f"Beneficiary: {profile['occupation']}")
    if primary_category:
        intent_parts.append(f"Domain: {primary_category}")

    intent_summary = " + ".join(intent_parts) if intent_parts else "General scheme discovery"

    return {
        "language": detected_lang,
        "query": query,
        "categories": categories,
        "primary_category": primary_category,
        "profile": profile,
        "intent_summary": intent_summary
    }
