"""
Embedded High-Performance Vector Store for BHASHA SAHITA.
Features:
- Dense vector similarity search using NumPy
- BM25 / Inverted Index keyword search
- Reciprocal Rank Fusion (RRF) hybrid retrieval
- Full metadata filtering across all 10 scheme criteria
- Disk persistence for fast cold-starts
"""
import os
import re
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict
import numpy as np

from .base import BaseVectorStore
from ..embeddings.generator import MultilingualEmbeddingGenerator

STORE_PATH = Path(__file__).parent.parent.parent / "data" / "vector_store.npz"
META_PATH = Path(__file__).parent.parent.parent / "data" / "vector_store_chunks.json"


class LocalVectorStore(BaseVectorStore):
    """Local embedded vector store with dense, sparse, and hybrid capabilities."""

    def __init__(self, embedding_generator: Optional[MultilingualEmbeddingGenerator] = None):
        self.embedding_gen = embedding_generator or MultilingualEmbeddingGenerator()
        self.chunks: List[Dict[str, Any]] = []
        self.embeddings: Optional[np.ndarray] = None
        self.inverted_index: Dict[str, List[int]] = defaultdict(list)
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: Optional[np.ndarray] = None) -> int:
        """Adds chunks, computes embeddings if omitted, and indexes for BM25."""
        if not chunks:
            return 0

        start_idx = len(self.chunks)
        self.chunks.extend(chunks)

        if embeddings is None:
            texts = [c.get("text", "") for c in chunks]
            new_embeddings = self.embedding_gen.embed_batch(texts)
        else:
            new_embeddings = embeddings

        if self.embeddings is None:
            self.embeddings = new_embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, new_embeddings])

        # Build Inverted Index for BM25
        for i, c in enumerate(chunks):
            idx = start_idx + i
            tokens = self._tokenize(c.get("text", ""))
            self.doc_lengths.append(len(tokens))
            seen = set()
            for t in tokens:
                if t not in seen:
                    self.inverted_index[t].append(idx)
                    seen.add(t)

        self.avg_doc_len = float(np.mean(self.doc_lengths)) if self.doc_lengths else 1.0
        return len(chunks)

    def _tokenize(self, text: str) -> List[str]:
        """Simple multilingual tokenization."""
        return re.findall(r"[\w\u0900-\u0D7F]+", text.lower())

    def _matches_filters(self, metadata: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
        """Evaluates whether chunk metadata meets all 10 filter criteria."""
        if not filters:
            return True

        # 1. Category
        if filters.get("category") and metadata.get("category"):
            if filters["category"].lower() != metadata.get("category", "").lower():
                return False

        # 2. Level (Central / State)
        if filters.get("level") and metadata.get("level"):
            if filters["level"].lower() != metadata.get("level", "").lower():
                return False

        # 3. State
        if filters.get("state") and metadata.get("state"):
            s_filter = filters["state"].lower()
            s_meta = metadata.get("state", "").lower()
            if s_meta not in ("all", "all india", s_filter):
                return False

        # 4. District
        if filters.get("district") and metadata.get("district"):
            if filters["district"].lower() != metadata.get("district", "").lower():
                return False

        # 5. Beneficiary
        if filters.get("beneficiary") and metadata.get("beneficiary"):
            b_list = [b.lower() for b in metadata.get("beneficiary", [])]
            if filters["beneficiary"].lower() not in b_list:
                return False

        # 6. Age Group
        if filters.get("age_group") and metadata.get("conditions"):
            # Condition check handled in scheme engine
            pass

        # 7. Family Income
        if filters.get("family_income") is not None and metadata.get("max_income"):
            try:
                if float(filters["family_income"]) > float(metadata["max_income"]):
                    return False
            except (ValueError, TypeError):
                pass

        # 8. Social Category
        if filters.get("social_category") and metadata.get("social_category"):
            sc = metadata.get("social_category")
            req = filters["social_category"]
            if isinstance(sc, list) and req not in sc and "all" not in [x.lower() for x in sc]:
                return False

        # 9. Benefit Type
        if filters.get("benefit_type") and metadata.get("benefit_type"):
            if filters["benefit_type"].lower() != metadata.get("benefit_type", "").lower():
                return False

        # 10. Application Status
        if filters.get("status") and metadata.get("status"):
            if filters["status"].lower() != metadata.get("status", "").lower():
                return False

        return True

    def search_vector(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Dense cosine similarity search with metadata filtering."""
        if self.embeddings is None or len(self.chunks) == 0:
            return []

        # Vector dot product (embeddings are unit normalized)
        scores = np.dot(self.embeddings, query_vector)
        # Sort descending
        ranked_indices = np.argsort(-scores)

        results = []
        for idx in ranked_indices:
            chunk = self.chunks[idx]
            if self._matches_filters(chunk.get("metadata", {}), filters):
                res = dict(chunk)
                res["score"] = float(scores[idx])
                res["retrieval_mode"] = "vector"
                results.append(res)
                if len(results) >= top_k:
                    break

        return results

    def search_keyword(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """BM25 keyword search across chunks with metadata filtering."""
        if not self.chunks or not query:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        n_docs = len(self.chunks)
        k1 = 1.5
        b = 0.75

        doc_scores: Dict[int, float] = defaultdict(float)

        for t in tokens:
            doc_list = self.inverted_index.get(t, [])
            df = len(doc_list)
            if df == 0:
                continue
            idf = math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)

            for doc_idx in doc_list:
                doc_text = self.chunks[doc_idx].get("text", "").lower()
                tf = doc_text.count(t)
                dl = self.doc_lengths[doc_idx] if doc_idx < len(self.doc_lengths) else self.avg_doc_len
                score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (dl / self.avg_doc_len)))
                doc_scores[doc_idx] += score

        ranked = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        results = []
        for doc_idx, score in ranked:
            chunk = self.chunks[doc_idx]
            if self._matches_filters(chunk.get("metadata", {}), filters):
                res = dict(chunk)
                res["score"] = float(score)
                res["retrieval_mode"] = "bm25"
                results.append(res)
                if len(results) >= top_k:
                    break

        return results

    def search_hybrid(
        self,
        query: str,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        alpha: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Reciprocal Rank Fusion (RRF) combining dense vector and BM25 scores:
        RRF_score(d) = alpha / (60 + rank_dense) + (1 - alpha) / (60 + rank_bm25)
        """
        vec_results = self.search_vector(query_vector, top_k=top_k * 2, filters=filters)
        bm25_results = self.search_keyword(query, top_k=top_k * 2, filters=filters)

        rrf_scores: Dict[str, float] = defaultdict(float)
        chunk_map: Dict[str, Dict[str, Any]] = {}
        k_rrf = 60

        for rank, item in enumerate(vec_results):
            cid = item["chunk_id"]
            chunk_map[cid] = item
            rrf_scores[cid] += alpha * (1.0 / (k_rrf + rank + 1))

        for rank, item in enumerate(bm25_results):
            cid = item["chunk_id"]
            if cid not in chunk_map:
                chunk_map[cid] = item
            rrf_scores[cid] += (1.0 - alpha) * (1.0 / (k_rrf + rank + 1))

        # Sort by merged RRF score
        sorted_cids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)

        merged = []
        for cid in sorted_cids[:top_k]:
            item = dict(chunk_map[cid])
            item["score"] = rrf_scores[cid]
            item["retrieval_mode"] = "hybrid_rrf"
            merged.append(item)

        return merged

    def count(self) -> int:
        return len(self.chunks)

    def save(self, npz_path: Optional[Path] = None, json_path: Optional[Path] = None):
        """Saves embeddings and chunks to disk."""
        npz_p = npz_path or STORE_PATH
        json_p = json_path or META_PATH
        if self.embeddings is not None:
            np.savez_compressed(str(npz_p), embeddings=self.embeddings)
        json_p.write_text(json.dumps(self.chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, npz_path: Optional[Path] = None, json_path: Optional[Path] = None) -> bool:
        """Loads embeddings and chunks from disk if available."""
        npz_p = npz_path or STORE_PATH
        json_p = json_path or META_PATH
        if not npz_p.exists() or not json_p.exists():
            return False

        try:
            chunks = json.loads(json_p.read_text(encoding="utf-8"))
            data = np.load(str(npz_p))
            embeddings = data["embeddings"]
            self.chunks = []
            self.embeddings = None
            self.inverted_index = defaultdict(list)
            self.doc_lengths = []
            self.add_chunks(chunks, embeddings)
            return True
        except Exception:
            return False
