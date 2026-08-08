from functools import lru_cache

from langchain_ollama import ChatOllama

from config import Config


@lru_cache
def get_llm():
    """Cached handle to the local Ollama chat model (temperature=0 for
    deterministic, factual answers/topic/flashcard generation)."""
    return ChatOllama(
        model=Config.OLLAMA_MODEL, base_url=Config.OLLAMA_BASE_URL, temperature=0
    )
