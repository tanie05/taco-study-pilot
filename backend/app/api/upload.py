import os

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from config import Config
from app.extensions import db
from app.models import ResourceFile, Workspace
from app.tasks.celery_tasks import process_workspace

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/upload", methods=["POST"])
def upload():
    """Accept one or more PDFs, save them, and kick off async ingestion.
    Returns immediately with a workspace id the frontend can poll for status."""
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files provided"}), 400

    pdf_files = [f for f in files if f.filename.lower().endswith(".pdf")]
    if not pdf_files:
        return jsonify({"error": "Only PDF files are supported"}), 400

    # A workspace groups the uploaded files + the topics/embeddings derived from them.
    workspace = Workspace(status="processing")
    db.session.add(workspace)
    db.session.flush()  # assign workspace.id without committing yet

    workspace_dir = os.path.join(Config.STORAGE_DIR, workspace.id)
    os.makedirs(workspace_dir, exist_ok=True)

    for f in pdf_files:
        filename = secure_filename(f.filename)
        storage_path = os.path.join(workspace_dir, filename)
        f.save(storage_path)
        db.session.add(
            ResourceFile(workspace_id=workspace.id, filename=filename, storage_path=storage_path)
        )

    db.session.commit()

    # Heavy lifting (PDF text extraction, embedding, topic generation) happens
    # in a Celery worker; see app/tasks/celery_tasks.py:process_workspace.
    process_workspace.delay(workspace.id)

    return jsonify({"workspace_id": workspace.id, "status": "processing"}), 200
