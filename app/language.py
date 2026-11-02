"""
Language Detection for BHASHA SAHITA using FastText lid.176 neural model.
Supports 6 languages: English ('en'), Hindi ('hi'), Marathi ('mr'), Punjabi ('pa'), Telugu ('te'), Bengali ('bn').
"""
import os
import re
import unicodedata
from pathlib import Path
import numpy as np

try:
    import fasttext
    # Monkeypatch for NumPy 2.x compatibility in FastText.predict
    def _patched_predict(self, text, k=1, threshold=0.0, on_unicode_error='strict'):
        def check(entry):
            if entry.find('\n') != -1:
                entry = entry.replace('\n', ' ')
            return entry + '\n'
        if isinstance(text, list):
            text = [check(e) for e in text]
            return self.f.multilinePredict(text, k, threshold, on_unicode_error)
        else:
            text = check(text)
            predictions = self.f.predict(text, k, threshold, on_unicode_error)
            if predictions:
                probs, labels = zip(*predictions)
            else:
                probs, labels = ([], ())
            return labels, np.asarray(probs)

    fasttext.FastText._FastText.predict = _patched_predict
except ImportError:
    fasttext = None

MODEL_PATH = Path(__file__).parent.parent / "data" / "models" / "lid.176.ftz"
_FASTTEXT_MODEL = None

ROMAN_HINDI = {
    "mujhe", "chahiye", "chahie", "kya", "hai", "hain", "mere", "meri", "mera", "liye",
    "yojana", "paisa", "madad", "kisan", "saal", "nahi", "nahin", "mujhko", "batao",
    "kaise", "milega", "chhatravritti", "yojna", "kholna"
}

def get_fasttext_model():
    """Lazy-loads FastText lid.176 neural classifier."""
    global _FASTTEXT_MODEL
    if _FASTTEXT_MODEL is not None:
        return _FASTTEXT_MODEL

    if fasttext and MODEL_PATH.exists():
        try:
            _FASTTEXT_MODEL = fasttext.load_model(str(MODEL_PATH))
            return _FASTTEXT_MODEL
        except Exception:
            pass
    return None

def detect_language(text: str) -> str:
    """
    Detects language using FastText lid.176 pre-trained neural network.
    Returns: 'en', 'hi', 'mr', 'pa', 'te', 'bn'.
    """
    if not text:
        return "en"

    text = unicodedata.normalize("NFC", text)
    cleaned = text.strip().replace("\n", " ")

    # Check Romanized Hindi / Hinglish first
    words = re.findall(r"\b[a-zA-Z]+\b", cleaned.lower())
    if words and len(set(words) & ROMAN_HINDI) >= 1:
        return "hi"

    model = get_fasttext_model()
    if model:
        try:
            labels, probs = model.predict(cleaned, k=3)
            for lbl in labels:
                code = lbl.replace("__label__", "")
                if code in ("en", "hi", "mr", "pa", "te", "bn"):
                    # Marathi vs Hindi disambiguation for short Devanagari strings
                    if code == "hi" and "ळ" in cleaned:
                        return "mr"
                    return code
        except Exception:
            pass

    # Heuristic fallback if model not loaded
    if any("\u0A00" <= c <= "\u0A7F" for c in cleaned):
        return "pa"
    if any("\u0980" <= c <= "\u09FF" for c in cleaned):
        return "bn"
    if any("\u0C00" <= c <= "\u0C7F" for c in cleaned):
        return "te"
    if any("\u0900" <= c <= "\u097F" for c in cleaned):
        return "mr" if "ळ" in cleaned or "मला" in cleaned or "आहे" in cleaned else "hi"

    return "en"
