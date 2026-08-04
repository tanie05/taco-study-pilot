from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Workspace
from app.services.rag import answer_question

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """RAG chat endpoint: answers a question using only chunks retrieved
    from the workspace's documents (see app/services/rag.py)."""
    data = request.get_json(silent=True) or {}
    workspace_id = data.get("workspace_id")
    message = data.get("message")

    if not workspace_id or not message:
        return jsonify({"error": "workspace_id and message are required"}), 400

    workspace = db.session.get(Workspace, workspace_id)
    if workspace is None:
        return jsonify({"error": "Workspace not found"}), 404
    if workspace.status != "ready":
        return jsonify({"error": f"Workspace is not ready (status: {workspace.status})"}), 409

    answer = answer_question(workspace_id, message)
    return jsonify({"answer": answer})
