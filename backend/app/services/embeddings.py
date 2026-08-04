from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from config import Config


@lru_cache
def get_embedding_model():
    """Loads the HF embedding model once per process and reuses it
    (model loading is slow, so this is cached rather than done per-request)."""
    return HuggingFaceEmbeddings(model_name=Config.EMBEDDING_MODEL)
