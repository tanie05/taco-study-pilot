from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config import Config


@lru_cache
def get_qdrant_client():
    return QdrantClient(url=Config.QDRANT_URL)


def ensure_collection():
    """Creates the shared Qdrant collection on first use. All workspaces'
    chunks live in this one collection, scoped by a workspace_id filter
    (see app/services/rag.py:retrieve_chunks)."""
    client = get_qdrant_client()
    if not client.collection_exists(Config.QDRANT_COLLECTION):
        client.create_collection(
            collection_name=Config.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=Config.EMBEDDING_DIM, distance=Distance.COSINE),
        )
    return client
