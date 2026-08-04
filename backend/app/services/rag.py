from langchain_core.messages import HumanMessage, SystemMessage
from qdrant_client.models import FieldCondition, Filter, MatchValue

from config import Config
from app.services.embeddings import get_embedding_model
from app.services.llm import get_llm
from app.services.qdrant_client import get_qdrant_client


def retrieve_chunks(workspace_id, query, k=None):
    """Vector-search Qdrant for the chunks most relevant to `query`,
    restricted to this workspace's documents. Used for both chat answers
    and flashcard generation (see app/services/topics.py)."""
    client = get_qdrant_client()
    embedding_model = get_embedding_model()
    query_vector = embedding_model.embed_query(query)

    results = client.query_points(
        collection_name=Config.QDRANT_COLLECTION,
        query=query_vector,
        query_filter=Filter(
            must=[FieldCondition(key="workspace_id", match=MatchValue(value=workspace_id))]
        ),
        limit=k or Config.RETRIEVAL_K,
    )
    return [point.payload["text"] for point in results.points]


def answer_question(workspace_id, question):
    """Core RAG step: retrieve relevant chunks, then ask the LLM to answer
    using only that context (grounds the answer, discourages hallucination)."""
    chunks = retrieve_chunks(workspace_id, question)

    if not chunks:
        return "I don't have enough information to answer that question based on the provided documents."

    context = "\n\n".join(f"- {c}" for c in chunks)
    prompt = f"""Based on the following documents, please answer this question: {question}

Documents:
{context}

Provide a clear, helpful answer using only the information from these documents. If you can't find the answer in the documents, say "I don't have enough information to answer that question based on the provided documents."
"""

    llm = get_llm()
    messages = [
        SystemMessage(content="You are a helpful study assistant that answers questions based only on the provided documents."),
        HumanMessage(content=prompt),
    ]
    result = llm.invoke(messages)
    return result.content
