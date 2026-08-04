from flask import Blueprint, jsonify

from app.extensions import db
from app.models import Topic, Workspace

workspace_bp = Blueprint("workspace", __name__)


@workspace_bp.route("/workspace/<workspace_id>/status", methods=["GET"])
def get_status(workspace_id):
    """Polled by the frontend while background ingestion runs
    (status: processing -> ready or failed)."""
    workspace = db.session.get(Workspace, workspace_id)
    if workspace is None:
        return jsonify({"error": "Workspace not found"}), 404
    return jsonify(workspace.to_dict())


@workspace_bp.route("/workspace/<workspace_id>/topics", methods=["GET"])
def get_topics(workspace_id):
    """List the topics the LLM generated for this workspace once ingestion finished."""
    workspace = db.session.get(Workspace, workspace_id)
    if workspace is None:
        return jsonify({"error": "Workspace not found"}), 404
    topics = Topic.query.filter_by(workspace_id=workspace_id).all()
    return jsonify([t.to_dict() for t in topics])
