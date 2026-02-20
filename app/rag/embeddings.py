try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except Exception:
    CHROMADB_AVAILABLE = False

from app.config import get_settings


def get_embedding_function():
    """Return ChromaDB's default embedding function (all-MiniLM-L6-v2)."""
    if not CHROMADB_AVAILABLE:
        return None
    return embedding_functions.DefaultEmbeddingFunction()


def get_chroma_client():
    if not CHROMADB_AVAILABLE:
        return None
    settings = get_settings()
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def get_collection(client=None):
    if not CHROMADB_AVAILABLE:
        return None
    client = client or get_chroma_client()
    return client.get_or_create_collection(
        name="medical_knowledge",
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )
