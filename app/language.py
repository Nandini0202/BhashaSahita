"""
Language detection for BHASHA SAHITA: 6 languages (en, hi, mr, pa, te, bn) + Hinglish.
Uses Unicode script ranges, NFC normalization, and high-frequency functional marker words.
"""
import re
import unicodedata

SCRIPTS = {
    "pa": (0x0A00, 0x0A7F),  # Gurmukhi
    "bn": (0x0980, 0x09FF),  # Bengali-Assamese
    "te": (0x0C00, 0x0C7F),  # Telugu
    "deva": (0x0900, 0x097F) # Devanagari (Hindi / Marathi)
}

MARATHI_MARKERS = [
    "मला", "हवी", "हवे", "आहे", "आहेत", "साठी", "आणि", "काय", "माझ", "माझे", "माझी",
    "ळ", "नाही", "योजना", "मिळेल", "करावे", "शेतकरी", "पाहिजे", "कशी", "कसा"
]

HINDI_MARKERS = [
    "मुझे", "चाहिए", "है", "हैं", "के लिए", "और", "क्या", "मेरा", "मेरी", "मेरे",
    "नहीं", "हूँ", "योजना", "मिलेगा", "मिलेगी", "किसान", "कैसे", "बताओ", "करना"
]

PUNJABI_MARKERS = [
    "ਮੈਨੂੰ", "ਚਾਹੀਦੀ", "ਚਾਹੀਦਾ", "ਹੈ", "ਹਨ", "ਲਈ", "ਅਤੇ", "ਕੀ", "ਮੇਰਾ", "ਨਹੀਂ",
    "ਕਿਸਾਨਾਂ", "ਸਹਾਇਤਾ", "ਯੋਜਨਾ"
]

TELUGU_MARKERS = [
    "నాకు", "కావాలి", "ఉంది", "మరియు", "ఏమిటి", "నా", "కాదు", "రైతులకు", "సహాయం", "పథకం"
]

BENGALI_MARKERS = [
    "আমার", "দরকার", "চাই", "আছে", "এবং", "কি", "জন্য", "না", "কৃষকদের", "সাহায্য", "প্রকল্প"
]

ROMAN_HINDI = {
    "mujhe", "chahiye", "chahie", "kya", "hai", "hain", "mere", "meri", "mera", "liye",
    "yojana", "paisa", "madad", "kisan", "saal", "nahi", "nahin", "mujhko", "batao",
    "kaise", "milega", "chhatravritti", "yojna", "kholna"
}

def detect_language(text: str) -> str:
    """Detects primary language: 'en', 'hi', 'mr', 'pa', 'te', 'bn'."""
    if not text:
        return "en"
    # Normalize unicode to NFC (handles Bengali nuktas, Devanagari composition)
    text = unicodedata.normalize("NFC", text)
    counts = {k: 0 for k in SCRIPTS}
    latin = 0

    for ch in text:
        cp = ord(ch)
        for k, (lo, hi) in SCRIPTS.items():
            if lo <= cp <= hi:
                counts[k] += 1
        if ch.isascii() and ch.isalpha():
            latin += 1

    best = max(counts, key=counts.get)
    if counts[best] > latin and counts[best] > 0:
        if best != "deva":
            return best
        # Disambiguate Devanagari between Marathi and Hindi
        # Specific Marathi letter: ळ
        if "ळ" in text:
            return "mr"
        mr_score = sum(text.count(w) for w in MARATHI_MARKERS)
        hi_score = sum(text.count(w) for w in HINDI_MARKERS)
        return "mr" if mr_score > hi_score else "hi"

    # Check for Romanized Hindi / Hinglish vs English
    words = set(re.findall(r"[a-z]+", text.lower()))
    if words & ROMAN_HINDI:
        return "hi"
    return "en"
