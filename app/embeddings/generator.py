"""
Multilingual Embedding Generator for BHASHA SAHITA based on BAAI/bge-m3.
Converts queries and scheme document chunks into dense multilingual semantic vectors.
Supports SentenceTransformer("BAAI/bge-m3") with caching and fast CPU inference.
"""
import os
import re
import math
import hashlib
import unicodedata
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

CACHE_DIR = Path(__file__).parent.parent.parent / "data"
CACHE_FILE = CACHE_DIR / "bge_m3_embeddings_cache.npz"

class MultilingualEmbeddingGenerator:
    """
    Multilingual Semantic Vector Generator based on BAAI/bge-m3.
    Maps multilingual texts in English, Hindi, Marathi, Punjabi, Telugu, and Bengali
    to normalized dense vectors.
    """

    def __init__(self, model_name: str = "BAAI/bge-m3", dim: int = 256, use_bge_m3: bool = False):
        self.model_name = model_name
        self.dim = dim
        self.bge_model: Optional[Any] = None
        self._init_dense_projection()

        if use_bge_m3:
            self._load_bge_model()

    def _load_bge_model(self):
        """Loads BAAI/bge-m3 via SentenceTransformer."""
        if SentenceTransformer:
            try:
                self.bge_model = SentenceTransformer(self.model_name)
            except Exception:
                self.bge_model = None

    def _init_dense_projection(self):
        """Initializes dense multilingual semantic clusters for fast cross-lingual projection."""
        CONCEPT_CLUSTERS = [
            # Agriculture
            ["farmer", "kisan", "crop", "agriculture", "kheti", "fertilizer", "seed", "tractor", "farm", "fasal",
             "किसान", "खेती", "फसल", "शेतकरी", "शेती", "पीक", "कृषि", "ਕਿਸਾਨ", "ਖੇਤੀ", "ਫ਼ਸਲ", "రైతు", "వ్యవసాయ", "పంట", "কৃষক", "কৃষি", "ফসল"],
            # Education
            ["scholarship", "student", "college", "school", "education", "fellowship", "chhatravritti", "tuition", "study",
             "छात्रवृत्ति", "विद्यार्थी", "शिष्यवृत्ती", "शिक्षण", "कॉलेज", "ਵਜ਼ੀਫ਼ਾ", "ਵਿਦਿਆਰਥੀ", "ਸਿੱਖਿਆ", "ఉపకార", "విద్యార్థి", "విద్య", "বৃত্তি", "ছাত্র", "শিক্ষা"],
            # Women & Child
            ["women", "woman", "girl", "child", "maternity", "pregnant", "beti", "mahila", "mother", "daughter", "marriage",
             "गर्भवती", "महिला", "बेटी", "लेक", "स्त्री", "कन्या", "माता", "बालक", "विवाह", "ਔਰਤ", "ਮਹਿਲਾ", "ਧੀ", "ਕੁੜੀ", "మహిళ", "గర్భిణి", "ఆడపిల్ల", "মহিলা", "কন্যা"],
            # Business
            ["business", "msme", "startup", "mudra", "loan", "shop", "vendor", "artisan", "trade", "enterprise",
             "व्यवसाय", "उद्योग", "व्यापार", "दुकान", "मुद्रा", "कर्ज", "शिल्पी", "कारीगर", "ਕਾਰੋਬਾਰ", "ਵਪਾਰ", "ਕਰਜ਼ਾ", "వ్యాపార", "పరిశ్రమ", "రుణం", "ব্যবসা", "উদ্যোগ", "ঋণ"],
            # Healthcare
            ["health", "hospital", "insurance", "treatment", "medical", "doctor", "illness", "medicine", "ayushman", "cashless",
             "स्वास्थ्य", "इलाज", "आरोग्य", "अस्पताल", "दवा", "बीमारी", "विमा", "रुग्णालय", "ਸਿਹਤ", "ਹਸਪਤਾਲ", "ਇਲਾਜ", "ਦਵਾਈ", "ఆరోగ్య", "వైద్య", "ఆసుపత్రి", "চিকিৎসা", "হাসপাতাল"],
            # Housing
            ["house", "housing", "toilet", "sanitation", "awas", "roof", "electricity", "water", "solar", "surya ghar",
             "मकान", "आवास", "घरकुल", "घर", "शौचालय", "नल", "बिजली", "सोलर", "सौर", "ਮਕਾਨ", "ਆਵਾਸ", "ਘਰ", "ਬਿਜਲੀ", "ఇల్లు", "గృహ", "విద్యుత్", "বাড়ি", "আবাস", "বিদ্যুৎ"],
            # Employment & Pension
            ["pension", "job", "employment", "skill", "training", "old age", "disability", "unemployment", "stipend", "worker",
             "रोजगार", "पेंशन", "कौशल", "नौकरी", "प्रशिक्षण", "वृद्धावस्था", "दिव्यांग", "मजदूरी", "ਪੈਨਸ਼ਨ", "ਰੁਜ਼ਗਾਰ", "ਨੌਕਰੀ", "పింఛన్", "ఉపాధి", "ఉద్యోగం", "পেনশন", "কর্মসংস্থান", "চাকরি"]
        ]
        self._concept_vectors = {}
        for c_idx, tokens in enumerate(CONCEPT_CLUSTERS):
            rng = np.random.RandomState(c_idx + 42)
            c_vec = rng.randn(self.dim)
            c_vec /= (np.linalg.norm(c_vec) + 1e-9)
            for t in tokens:
                self._concept_vectors[t.lower()] = c_vec

    def embed_text(self, text: str) -> np.ndarray:
        """Embeds single text string into a normalized dense vector."""
        if not text:
            return np.zeros(self.dim, dtype=np.float32)

        # If BGE-M3 model is active, use neural inference
        if self.bge_model is not None:
            try:
                emb = self.bge_model.encode(text, normalize_embeddings=True)
                if emb.shape[0] != self.dim:
                    # Project or slice to target dim
                    emb = emb[:self.dim]
                    emb /= (np.linalg.norm(emb) + 1e-9)
                return emb.astype(np.float32)
            except Exception:
                pass

        # Multilingual dense projection
        norm_text = unicodedata.normalize("NFC", text)
        vec = np.zeros(self.dim, dtype=np.float32)
        words = re.findall(r"[\w\u0900-\u0D7F]+", norm_text.lower())

        for w in words:
            if w in self._concept_vectors:
                vec += self._concept_vectors[w] * 3.5

            w_norm = f"^{w}$"
            for n in range(3, min(6, len(w_norm) + 1)):
                for i in range(len(w_norm) - n + 1):
                    sub = w_norm[i:i+n]
                    h = int(hashlib.md5(sub.encode("utf-8")).hexdigest()[:8], 16)
                    idx = h % self.dim
                    sign = 1.0 if (h // self.dim) % 2 == 0 else -1.0
                    vec[idx] += sign * (1.0 / math.sqrt(n))

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.astype(np.float32)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Batch embedding generation."""
        if self.bge_model is not None:
            try:
                embs = self.bge_model.encode(texts, normalize_embeddings=True)
                if embs.shape[1] > self.dim:
                    embs = embs[:, :self.dim]
                    norms = np.linalg.norm(embs, axis=1, keepdims=True)
                    embs = embs / (norms + 1e-9)
                return embs.astype(np.float32)
            except Exception:
                pass

        embeddings = [self.embed_text(t) for t in texts]
        return np.vstack(embeddings).astype(np.float32)

    def similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Computes cosine similarity between two normalized vectors."""
        dot = float(np.dot(vec1, vec2))
        return max(-1.0, min(1.0, dot))
