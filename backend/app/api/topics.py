from flask import Blueprint, jsonify

from app.extensions import db
from app.models import Flashcard, Topic
from app.services.topics import generate_flashcards

topics_bp = Blueprint("topics", __name__)


@topics_bp.route("/topics/<topic_id>/generate", methods=["POST"])
def generate(topic_id):
    """Generate flashcards for a single topic on demand (not precomputed at ingestion time).
    Results are cached in the flashcards table so repeat requests skip the LLM."""
    topic = db.session.get(Topic, topic_id)
    if topic is None:
        return jsonify({"error": "Topic not found"}), 404

    if topic.flashcards:
        return jsonify({"topic": topic.title, "flashcards": [f.to_dict() for f in topic.flashcards]})

    cards = generate_flashcards(topic.workspace_id, topic.title)
    for card in cards:
        db.session.add(Flashcard(topic_id=topic.id, question=card["question"], answer=card["answer"]))
    db.session.commit()

    return jsonify({"topic": topic.title, "flashcards": cards})
