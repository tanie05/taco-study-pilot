from flask import Blueprint, jsonify

from app.extensions import db
from app.models import Topic
from app.services.topics import generate_flashcards

topics_bp = Blueprint("topics", __name__)


@topics_bp.route("/topics/<topic_id>/generate", methods=["POST"])
def generate(topic_id):
    """Generate flashcards for a single topic on demand (not precomputed at ingestion time)."""
    topic = db.session.get(Topic, topic_id)
    if topic is None:
        return jsonify({"error": "Topic not found"}), 404

    cards = generate_flashcards(topic.workspace_id, topic.title)
    # todo: save flashcards, so we dont have to generate after again and again
    return jsonify({"topic": topic.title, "flashcards": cards})
