import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # App metadata DB (workspaces, files, topics) — SQLite by default.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI", f"sqlite:///{BASE_DIR}/instance/app.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")  # Celery broker/result backend

    # Qdrant stores the document chunk embeddings used for retrieval.
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "study_chunks")

    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")  # local LLM used for chat/topics/flashcards
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    EMBEDDING_DIM = 384  # bge-small-en-v1.5 output dimension; must match Qdrant collection vector size

    STORAGE_DIR = os.path.join(BASE_DIR, os.getenv("STORAGE_DIR", "storage"))  # uploaded PDFs live here

    # Ingestion / RAG tuning knobs.
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 100
    RETRIEVAL_K = 5  # number of chunks pulled from Qdrant per query
    NUM_TOPICS = 8  # topics generated per workspace
    FLASHCARDS_PER_TOPIC = 15
