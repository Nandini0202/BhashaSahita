"""
Vector Store Factory for BHASHA SAHITA.
Automatically selects PostgreSQL + pgvector if available,
or falls back gracefully to the embedded LocalVectorStore.
"""
import os
from .base import BaseVectorStore
from .local_store import LocalVectorStore
from .pgvector_store import PgVectorStore
from ..embeddings.generator import MultilingualEmbeddingGenerator

_INSTANCE: BaseVectorStore | None = None

def get_vector_store() -> BaseVectorStore:
    """Returns singleton vector store instance."""
    global _INSTANCE
    if _INSTANCE is not None:
        return _INSTANCE

    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        pg_store = PgVectorStore(connection_url=db_url)
        if pg_store.is_available():
            _INSTANCE = pg_store
            return _INSTANCE

    # Default to LocalVectorStore
    local_store = LocalVectorStore(embedding_generator=MultilingualEmbeddingGenerator())
    # Try loading existing index from disk
    if not local_store.load():
        # Initialize by ingesting documents
        from ..ingestion.collector import SchemeDocumentCollector
        collector = SchemeDocumentCollector()
        chunks = collector.ingest_all_documents()
        local_store.add_chunks(chunks)
        local_store.save()

    _INSTANCE = local_store
    return _INSTANCE
