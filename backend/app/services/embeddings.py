from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from config import Config


@lru_cache
def get_embedding_model():
    """Loads the HF embedding model once per process and reuses it
    (model loading is slow, so this is cached rather than done per-request).

    Pinned to CPU: bge-small is tiny (33M params) so there's no real speed
    benefit from Apple's MPS backend, and MPS doesn't reliably support being
    used by multiple OS processes at once (Flask + Celery worker both load
    this model) — under concurrent access it can fail with
    "Cannot copy out of meta tensor; no data!" during model init.
    """
    return HuggingFaceEmbeddings(
        model_name=Config.EMBEDDING_MODEL, model_kwargs={"device": "cpu"}
    )
