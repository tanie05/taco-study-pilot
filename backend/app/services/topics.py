import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from config import Config
from app.services.llm import get_llm
from app.services.rag import retrieve_chunks

logger = logging.getLogger(__name__)


def _extract_json_array(text):
    """LLMs often wrap JSON in prose/markdown fences; pull out just the
    first [...] array so we can parse it reliably."""
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found in LLM output: {text[:200]}")
    return json.loads(match.group(0))


def generate_topics(workspace_id, sample_chunks):
    """Called once during ingestion (see app/tasks/celery_tasks.py) to derive
    a fixed set of study topics from a sample of the workspace's chunks.

    sample_chunks: list of chunk texts representative of the workspace content
    """
    logger.info(
        "generate_topics: workspace %s, sampling %d chunk(s) for %d topic(s)",
        workspace_id,
        len(sample_chunks),
        Config.NUM_TOPICS,
    )
    context = "\n\n".join(f"- {c}" for c in sample_chunks)
    prompt = f"""Based on the following study material, identify the {Config.NUM_TOPICS} most important topics a student should study.

Study material:
{context}

Return ONLY a JSON array of short topic title strings, e.g. ["Topic A", "Topic B"]. No other text.
"""
    llm = get_llm()
    messages = [
        SystemMessage(content="You are a study assistant that extracts key topics from study material."),
        HumanMessage(content=prompt),
    ]
    result = llm.invoke(messages)
    titles = _extract_json_array(result.content)
    titles = [str(t).strip() for t in titles if str(t).strip()][: Config.NUM_TOPICS]
    logger.info("generate_topics: workspace %s -> %s", workspace_id, titles)
    return titles


def generate_flashcards(workspace_id, topic_title):
    """Called on demand (POST /topics/<id>/generate) rather than during
    ingestion, so flashcards are only generated for topics the user opens."""
    chunks = retrieve_chunks(workspace_id, topic_title, k=Config.RETRIEVAL_K * 2)
    context = "\n\n".join(f"- {c}" for c in chunks)

    prompt = f"""Based on the following study material about "{topic_title}", generate {Config.FLASHCARDS_PER_TOPIC} interview/study-oriented flashcards.

Study material:
{context}

Return ONLY a JSON array of objects with "question" and "answer" fields, e.g.
[{{"question": "...", "answer": "..."}}]. No other text.
"""
    llm = get_llm()
    messages = [
        SystemMessage(content="You are a study assistant that creates flashcards from study material."),
        HumanMessage(content=prompt),
    ]
    result = llm.invoke(messages)
    cards = _extract_json_array(result.content)
    return [c for c in cards if "question" in c and "answer" in c]
