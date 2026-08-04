import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from qdrant_client.models import PointStruct

from config import Config
from app.services.embeddings import get_embedding_model
from app.services.qdrant_client import ensure_collection


def extract_text(file_path):
    """Pull raw text out of a PDF, page by page (pages with no extractable text are skipped)."""
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def chunk_text(text):
    """Split extracted text into overlapping chunks sized for embedding/retrieval."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP,
    )
    return [c for c in splitter.split_text(text) if c.strip()]


def embed_and_store(workspace_id, chunks_with_source):
    """Embed each chunk and upsert it into Qdrant, tagged with workspace_id
    so retrieval can filter to only this workspace's documents.

    chunks_with_source: list of (chunk_text, filename) tuples
    """
    if not chunks_with_source:
        return

    client = ensure_collection()
    embedding_model = get_embedding_model()

    texts = [c for c, _ in chunks_with_source]
    vectors = embedding_model.embed_documents(texts)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={"workspace_id": workspace_id, "text": text, "source": source},
        )
        for vector, (text, source) in zip(vectors, chunks_with_source)
    ]

    client.upsert(collection_name=Config.QDRANT_COLLECTION, points=points)
