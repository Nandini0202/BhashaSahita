"""
Vector Store Base Interface for BHASHA SAHITA.
Defines common contract for local and PostgreSQL + pgvector implementations.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import numpy as np

class BaseVectorStore(ABC):
    """Abstract interface for storing and retrieving document chunks with metadata."""

    @abstractmethod
    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: Optional[np.ndarray] = None) -> int:
        """Adds chunks and their embeddings to the vector store."""
        pass

    @abstractmethod
    def search_vector(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Dense semantic vector similarity search with optional metadata filters."""
        pass

    @abstractmethod
    def search_keyword(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Sparse keyword / BM25 search with optional metadata filters."""
        pass

    @abstractmethod
    def search_hybrid(
        self,
        query: str,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        alpha: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Hybrid search combining dense vector search and sparse keyword search."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Returns total number of chunks stored."""
        pass
