"""
Multilingual i18n support for BHASHA SAHITA (6 languages: en, hi, mr, pa, te, bn).
Handles scheme translations, localized categories, and regional text representations.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

LANGUAGES = {
    "en": {"name": "English", "native": "English", "code": "en"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "code": "hi"},
    "mr": {"name": "Marathi", "native": "मराठी", "code": "mr"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "code": "pa"},
    "te": {"name": "Telugu", "native": "తెలుగు", "code": "te"},
    "bn": {"name": "Bengali", "native": "বাংলা", "code": "bn"},
}

CATEGORIES = {
    "education": {
        "en": "Education & Scholarships",
        "hi": "शिक्षा और छात्रवृत्ति",
        "mr": "शिक्षण आणि शिष्यवृत्ती",
        "pa": "ਸਿੱਖਿਆ ਅਤੇ ਵਜ਼ੀਫ਼ੇ",
        "te": "విద్య మరియు ఉపకార వేతనాలు",
        "bn": "শিক্ষা ও বৃত্তি"
    },
    "agriculture": {
        "en": "Agriculture & Farmers",
        "hi": "कृषि और किसान कल्याण",
        "mr": "कृषी आणि शेतकरी कल्याण",
        "pa": "ਖੇਤੀਬਾੜੀ ਅਤੇ ਕਿਸਾਨ ਭਲਾਈ",
        "te": "వ్యవసాయం మరియు రైతు సంక్షేమం",
        "bn": "কৃষি ও কৃষক কল্যাণ"
    },
    "women_child": {
        "en": "Women & Child Welfare",
        "hi": "महिला एवं बाल विकास",
        "mr": "महिला आणि बाल विकास",
        "pa": "ਮਹਿਲਾ ਅਤੇ ਬਾਲ ਵਿਕਾਸ",
        "te": "మహిళా మరియు శిశు సంక్షేమం",
        "bn": "নারী ও শিশু কল্যাণ"
    },
    "business": {
        "en": "Business & Entrepreneurship",
        "hi": "व्यापार और स्वरोजगार",
        "mr": "व्यवसाय आणि उद्योग",
        "pa": "ਵਪਾਰ ਅਤੇ ਉੱਦਮਤਾ",
        "te": "వ్యాపారం మరియు వ్యవస్థాపకత",
        "bn": "ব্যবসা ও উদ্যোগ"
    },
    "healthcare": {
        "en": "Healthcare & Insurance",
        "hi": "स्वास्थ्य और चिकित्सा बीमा",
        "mr": "आरोग्य आणि वैद्यकीय विमा",
        "pa": "ਸਿਹਤ ਅਤੇ ਡਾਕਟਰੀ ਬੀਮਾ",
        "te": "ఆరోగ్యం మరియు వైద్య భీమా",
        "bn": "স্বাস্থ্য ও চিকিৎসা বীমা"
    },
    "housing": {
        "en": "Housing & Basic Needs",
        "hi": "आवास और बुनियादी सुविधाएं",
        "mr": "गृहनिर्माण आणि मूलभूत सुविधा",
        "pa": "ਰਿਹਾਇਸ਼ ਅਤੇ ਬੁਨਿਆਦੀ ਲੋੜਾਂ",
        "te": "గృహనిర్మాణం మరియు ప్రాథమిక అవసరాలు",
        "bn": "আবাসন ও মৌলিক চাহিদা"
    },
    "employment_pension": {
        "en": "Employment, Pension & Social Security",
        "hi": "रोजगार, पेंशन और सामाजिक सुरक्षा",
        "mr": "रोजगार, निवृत्तीवेतन आणि सामाजिक सुरक्षा",
        "pa": "ਰੁਜ਼ਗਾਰ, ਪੈਨਸ਼ਨ ਅਤੇ ਸਮਾਜਿਕ ਸੁਰੱਖਿਆ",
        "te": "ఉపాధి, పింఛన్లు మరియు సామాజిక భద్రత",
        "bn": "কর্মসংস্থান, পেনশন ও সামাজিক সুরক্ষা"
    }
}

BENEFIT_TYPES = {
    "grant": {"en": "Grant", "hi": "अनुदान", "mr": "अनुदान", "pa": "ਗ੍ਰਾਂਟ", "te": "గ్రాంట్", "bn": "অনুদান"},
    "subsidy": {"en": "Subsidy", "hi": "सब्सिडी", "mr": "सबसिडी", "pa": "ਸਬਸਿਡੀ", "te": "సబ్సిడీ", "bn": "ভর্তুকি"},
    "loan": {"en": "Loan", "hi": "ऋण (कर्ज)", "mr": "कर्ज", "pa": "ਕਰਜ਼ਾ", "te": "రుణం", "bn": "ঋণ"},
    "pension": {"en": "Pension", "hi": "पेंशन", "mr": "पेन्शन", "pa": "ਪੈਨਸ਼ਨ", "te": "పింఛన్", "bn": "পেনশন"},
    "scholarship": {"en": "Scholarship", "hi": "छात्रवृत्ति", "mr": "शिष्यवृत्ती", "pa": "ਵਜ਼ੀਫ਼ਾ", "te": "స్కాలర్‌షిప్", "bn": "বৃত্তি"},
    "insurance": {"en": "Insurance", "hi": "बीमा", "mr": "विमा", "pa": "ਬੀਮਾ", "te": "భీమా", "bn": "বীমা"}
}

STATUS_LABELS = {
    "year_round": {"en": "Year-round Active", "hi": "साल भर सक्रिय", "mr": "वर्षभर सक्रिय", "pa": "ਸਾਰਾ ਸਾਲ ਸਰਗਰਮ", "te": "ఏడాది పొడవునా క్రియాశీలకం", "bn": "সারা বছর সক্রিয়"},
    "open": {"en": "Open Window", "hi": "आवेदन खुला है", "mr": "अर्ज सुरू आहेत", "pa": "ਅਰਜ਼ੀਆਂ ਖੁੱਲ੍ਹੀਆਂ ਹਨ", "te": "దరఖాస్తులు ప్రారంభమయ్యాయి", "bn": "আবেদন প্রক্রিয়া চালু আছে"},
    "seasonal": {"en": "Seasonal", "hi": "मौसमी योजना", "mr": "हंगामी योजना", "pa": "ਮੌਸਮੀ ਯੋਜਨਾ", "te": "సీజనల్ పథకం", "bn": "মৌসুমি প্রকল্প"},
    "closed_check_extension": {"en": "Closed / Check Extension", "hi": "समाप्त / विस्तार देखें", "mr": "बंद / मुदतवाढ तपासा", "pa": "ਬੰਦ / ਵਾਧਾ ਦੇਖੋ", "te": "ముగిసింది / పొడిగింపు చూడండి", "bn": "বন্ধ / মেয়াদ বৃদ্ধি দেখুন"},
    "needs_verification": {"en": "Needs Verification", "hi": "पुष्टि आवश्यक", "mr": "पडताळणी आवश्यक", "pa": "ਪੜਤਾਲ ਜ਼ਰੂਰੀ", "te": "ధృవీకరణ అవసరం", "bn": "যাচাই প্রয়োজন"}
}

VERDICTS = {
    "meets_listed_conditions": {
        "en": "Meets Listed Conditions",
        "hi": "सूचीबद्ध शर्तें पूरी",
        "mr": "सूचीबद्ध अटी पूर्ण",
        "pa": "ਸੂਚੀਬੱਧ ਸ਼ਰਤਾਂ ਪੂਰੀਆਂ",
        "te": "జాబితా చేసిన నిబంధనలు సరిపోలాయి",
        "bn": "তালিকাভুক্ত শর্ত পূরণ হয়েছে"
    },
    "possibly_eligible": {
        "en": "Possibly Eligible",
        "hi": "संभावित पात्र",
        "mr": "संभाव्य पात्र",
        "pa": "ਸੰਭਾਵੀ ਯੋਗ",
        "te": "అర్హత ఉండవచ్చు",
        "bn": "সম্ভাব্য যোগ্য"
    },
    "not_eligible": {
        "en": "Not Eligible",
        "hi": "पात्र नहीं",
        "mr": "अपात्र",
        "pa": "ਯੋਗ ਨਹੀਂ",
        "te": "అర్హత లేదు",
        "bn": "যোগ্য নন"
    }
}

_TRANSLATIONS = {}
def _load_translations():
    global _TRANSLATIONS
    if not _TRANSLATIONS:
        trans_file = DATA_DIR / "scheme_translations.json"
        if trans_file.exists():
            _TRANSLATIONS = json.loads(trans_file.read_text(encoding="utf-8"))
    return _TRANSLATIONS

def get_supported_languages() -> dict:
    return LANGUAGES

def get_category_label(cat_key: str, lang: str = "en") -> str:
    lang = lang if lang in LANGUAGES else "en"
    return CATEGORIES.get(cat_key, {}).get(lang, cat_key)

def get_benefit_type_label(btype: str, lang: str = "en") -> str:
    lang = lang if lang in LANGUAGES else "en"
    return BENEFIT_TYPES.get(btype, {}).get(lang, btype)

def get_status_label(status: str, lang: str = "en") -> str:
    lang = lang if lang in LANGUAGES else "en"
    return STATUS_LABELS.get(status, {}).get(lang, status)

def get_verdict_label(verdict: str, lang: str = "en") -> str:
    lang = lang if lang in LANGUAGES else "en"
    return VERDICTS.get(verdict, {}).get(lang, verdict)

def get_translation(scheme_id: str, lang: str = "en") -> dict:
    t = _load_translations()
    scheme_t = t.get(scheme_id, {})
    if lang in scheme_t:
        return scheme_t[lang]
    return scheme_t.get("en", {"name": scheme_id, "purpose": "", "simplified_text": "", "human_validated": False})

def localize_scheme(scheme: dict, lang: str = "en") -> dict:
    """Returns a scheme dictionary with name and purpose translated into the requested language."""
    tr = get_translation(scheme.get("id", ""), lang)
    localized = dict(scheme)
    localized["name_local"] = tr.get("name", scheme.get("name_en"))
    localized["purpose_local"] = tr.get("purpose", scheme.get("purpose"))
    localized["simplified_text"] = tr.get("simplified_text", scheme.get("purpose"))
    localized["category_local"] = get_category_label(scheme.get("category", ""), lang)
    localized["benefit_type_local"] = get_benefit_type_label(scheme.get("benefit_type", ""), lang)
    localized["status_local"] = get_status_label(scheme.get("status", ""), lang)
    localized["lang"] = lang
    return localized
