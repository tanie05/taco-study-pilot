import os

from flask import Blueprint, g, jsonify, request
from werkzeug.utils import secure_filename

from config import Config
from app.extensions import db
from app.models import ResourceFile, Topic, Workspace
from app.services.qdrant_client import ensure_collection
from app.tasks.celery_tasks import process_workspace
from qdrant_client.models import FieldCondition, Filter, MatchValue

upload_bp = Blueprint("upload", __name__)


def _save_pdfs(workspace_id, pdf_files):
    """Save PDFs into the workspace's storage dir and create ResourceFile
    rows for them. Shared by both a fresh /upload and /workspace/<id>/files."""
    workspace_dir = os.path.join(Config.STORAGE_DIR, workspace_id)
    os.makedirs(workspace_dir, exist_ok=True)

    for f in pdf_files:
        filename = secure_filename(f.filename)
        storage_path = os.path.join(workspace_dir, filename)
        f.save(storage_path)
        db.session.add(
            ResourceFile(workspace_id=workspace_id, filename=filename, storage_path=storage_path)
        )


@upload_bp.route("/upload", methods=["POST"])
def upload():
    """Accept one or more PDFs, save them, and kick off async ingestion.
    Returns immediately with a workspace id the frontend can poll for status.
    A caller (guest or, later, a signed-up user) may only own one workspace
    at a time — see app/api/workspace.py's add-files/delete endpoints for
    how to extend or replace an existing one."""
    existing = Workspace.query.filter_by(user_id=g.current_user.id).first()
    if existing is not None:
        return jsonify({
            "error": "You already have a workspace. Add files to it or delete it before starting a new one.",
            "workspace_id": existing.id,
        }), 409

    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files provided"}), 400

    pdf_files = [f for f in files if f.filename.lower().endswith(".pdf")]
    if not pdf_files:
        return jsonify({"error": "Only PDF files are supported"}), 400

    # A workspace groups the uploaded files + the topics/embeddings derived from them.
    workspace = Workspace(status="processing", user_id=g.current_user.id)
    db.session.add(workspace)
    db.session.flush()  # assign workspace.id without committing yet

    _save_pdfs(workspace.id, pdf_files)
    db.session.commit()

    # Heavy lifting (PDF text extraction, embedding, topic generation) happens
    # in a Celery worker; see app/tasks/celery_tasks.py:process_workspace.
    process_workspace.delay(workspace.id)

    return jsonify({"workspace_id": workspace.id, "status": "processing"}), 200


@upload_bp.route("/workspace/<workspace_id>/files", methods=["POST"])
def add_files(workspace_id):
    """Add more PDFs to an existing workspace (same topic) and reprocess
    everything from scratch — old + new files together. Topic generation
    re-runs and replaces the previous topics/flashcards, per design."""
    workspace = db.session.get(Workspace, workspace_id)
    if workspace is None or workspace.user_id != g.current_user.id:
        return jsonify({"error": "Workspace not found"}), 404
    if workspace.status == "processing":
        return jsonify({"error": "Workspace is already processing"}), 409

    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files provided"}), 400

    pdf_files = [f for f in files if f.filename.lower().endswith(".pdf")]
    if not pdf_files:
        return jsonify({"error": "Only PDF files are supported"}), 400

    _save_pdfs(workspace.id, pdf_files)

    # Wipe stale derived state before reprocessing: the Celery task always
    # re-reads *all* ResourceFile rows for the workspace from scratch, so
    # leftover vectors would be duplicated and leftover topics would be
    # stale/out of sync with the newly combined content.
    client = ensure_collection()
    client.delete(
        collection_name=Config.QDRANT_COLLECTION,
        points_selector=Filter(must=[FieldCondition(key="workspace_id", match=MatchValue(value=workspace.id))]),
    )
    # Delete Topic objects one at a time (not a bulk .filter_by(...).delete())
    # so the ORM cascade actually fires and cleans up their Flashcard rows too.
    for topic in Topic.query.filter_by(workspace_id=workspace.id).all():
        db.session.delete(topic)

    workspace.status = "processing"
    workspace.stage = "queued"
    workspace.stage_message = None
    workspace.error_message = None
    workspace.topics_stage = "pending"
    workspace.topics_message = None
    workspace.topics_error = None
    db.session.commit()

    process_workspace.delay(workspace.id)

    return jsonify({"workspace_id": workspace.id, "status": "processing"}), 200
