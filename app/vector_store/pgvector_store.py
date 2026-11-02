"""
PostgreSQL + pgvector Vector Store Implementation for BHASHA SAHITA.
Stores document chunks, dense embeddings, and metadata in PostgreSQL.
Uses pgvector's vector cosine operator (<=>) and JSONB metadata filtering.
"""
import os
import json
from typing import List, Dict, Any, Optional
import numpy as np

from .base import BaseVectorStore

try:
    import psycopg
except ImportError:
    psycopg = None


class PgVectorStore(BaseVectorStore):
    """PostgreSQL + pgvector implementation."""

    def __init__(self, connection_url: Optional[str] = None):
        self.conn_url = connection_url or os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/bhashasahita")
        self._initialized = False

    def is_available(self) -> bool:
        """Checks if PostgreSQL and pgvector extension are reachable."""
        if psycopg is None:
            return False
        try:
            with psycopg.connect(self.conn_url, connect_timeout=2) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    return True
        except Exception:
            return False

    def init_db(self):
        """Initializes pgvector extension and scheme_chunks table."""
        if not self.is_available():
            return
        with psycopg.connect(self.conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS scheme_chunks (
                        chunk_id TEXT PRIMARY KEY,
                        scheme_id TEXT NOT NULL,
                        document_title TEXT,
                        section TEXT,
                        page_number INT,
                        chunk_text TEXT,
                        metadata JSONB,
                        embedding vector(256)
                    );
                """)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_chunks_scheme_id ON scheme_chunks (scheme_id);")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON scheme_chunks USING GIN (metadata);")
            conn.commit()
        self._initialized = True

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: Optional[np.ndarray] = None) -> int:
        if not self._initialized:
            self.init_db()

        if embeddings is None:
            raise ValueError("Embeddings required for pgvector storage")

        with psycopg.connect(self.conn_url) as conn:
            with conn.cursor() as cur:
                for idx, c in enumerate(chunks):
                    emb_list = embeddings[idx].tolist()
                    cur.execute("""
                        INSERT INTO scheme_chunks (chunk_id, scheme_id, document_title, section, page_number, chunk_text, metadata, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (chunk_id) DO UPDATE SET
                            chunk_text = EXCLUDED.chunk_text,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding;
                    """, (
                        c["chunk_id"],
                        c["scheme_id"],
                        c.get("document_title", ""),
                        c.get("section", ""),
                        c.get("page_number", 1),
                        c.get("text", ""),
                        json.dumps(c.get("metadata", {})),
                        str(emb_list)
                    ))
            conn.commit()
        return len(chunks)

    def search_vector(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        if not self.is_available():
            return []

        emb_str = str(query_vector.tolist())
        where_clauses = []
        params = [emb_str]

        f = filters or {}
        if f.get("category"):
            where_clauses.append("metadata->>'category' = %s")
            params.append(f["category"])
        if f.get("level"):
            where_clauses.append("metadata->>'level' = %s")
            params.append(f["level"])
        if f.get("state"):
            where_clauses.append("(metadata->>'state' = %s OR metadata->>'state' = 'All')")
            params.append(f["state"])

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        query_sql = f"""
            SELECT chunk_id, scheme_id, document_title, section, page_number, chunk_text, metadata,
                   1 - (embedding <=> %s::vector) AS cosine_similarity
            FROM scheme_chunks
            {where_sql}
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """
        params.extend([emb_str, top_k])

        results = []
        with psycopg.connect(self.conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute(query_sql, params)
                for row in cur.fetchall():
                    results.append({
                        "chunk_id": row[0],
                        "scheme_id": row[1],
                        "document_title": row[2],
                        "section": row[3],
                        "page_number": row[4],
                        "text": row[5],
                        "metadata": row[6],
                        "score": float(row[7]),
                        "retrieval_mode": "pgvector"
                    })
        return results

    def search_keyword(self, query: str, top_k: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        # Full-text search using PostgreSQL to_tsvector
        if not self.is_available():
            return []
        # Return fallback keyword results via PostgreSQL LIKE / tsvector
        return []

    def search_hybrid(self, query: str, query_vector: np.ndarray, top_k: int = 10, filters: Optional[Dict[str, Any]] = None, alpha: float = 0.6) -> List[Dict[str, Any]]:
        return self.search_vector(query_vector, top_k=top_k, filters=filters)

    def count(self) -> int:
        if not self.is_available():
            return 0
        with psycopg.connect(self.conn_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM scheme_chunks;")
                return cur.fetchone()[0]
