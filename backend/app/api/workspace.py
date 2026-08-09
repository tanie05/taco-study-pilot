import json
import logging
import os
import shutil

from flask import Blueprint, Response, g, jsonify

from config import Config
from app.extensions import db
from app.models import Topic, Workspace
from app.services.events import subscribe
from app.services.qdrant_client import ensure_collection
from qdrant_client.models import FieldCondition, Filter, MatchValue

workspace_bp = Blueprint("workspace", __name__)

logger = logging.getLogger(__name__)

TERMINAL_STAGES = {"ready", "failed"}
KEEPALIVE_SECONDS = 15


def _get_owned_workspace(workspace_id):
    """Look up a workspace and verify it belongs to the caller. Returns
    None (not the workspace) on any mismatch — callers should respond 404
    either way so a wrong/guessed id doesn't reveal whether it exists."""
    workspace = db.session.get(Workspace, workspace_id)
    if workspace is None or workspace.user_id != g.current_user.id:
        return None
    return workspace


@workspace_bp.route("/workspace/mine", methods=["GET"])
def get_mine():
    """Returns the caller's single workspace, if any — used by the
    frontend on load to restore state across reloads via the guest_id
    cookie instead of always starting at the upload screen."""
    workspace = Workspace.query.filter_by(user_id=g.current_user.id).first()
    if workspace is None:
        return jsonify({"error": "No workspace"}), 404
    return jsonify(workspace.to_dict())


@workspace_bp.route("/workspace/<workspace_id>/status", methods=["GET"])
def get_status(workspace_id):
    """One-off status check (status: processing -> ready or failed). The
    frontend now uses GET /workspace/<id>/events for live updates instead
    of polling this in a loop."""
    workspace = _get_owned_workspace(workspace_id)
    if workspace is None:
        return jsonify({"error": "Workspace not found"}), 404
    return jsonify(workspace.to_dict())


@workspace_bp.route("/workspace/<workspace_id>", methods=["DELETE"])
def delete_workspace(workspace_id):
    """Permanently delete a workspace: its Qdrant vectors, uploaded files
    on disk, and DB rows (ResourceFile/Topic/Flashcard cascade via the
    existing ORM relationships since this is a single-object delete)."""
    workspace = _get_owned_workspace(workspace_id)
    if workspace is None:
        return jsonify({"error": "Workspace not found"}), 404
    if workspace.status == "processing":
        # The in-flight Celery task holds a reference to this workspace_id
        # and would otherwise keep writing to rows/vectors being deleted
        # out from under it.
        return jsonify({"error": "Cannot delete while processing"}), 409

    client = ensure_collection()
    client.delete(
        collection_name=Config.QDRANT_COLLECTION,
        points_selector=Filter(must=[FieldCondition(key="workspace_id", match=MatchValue(value=workspace_id))]),
    )

    workspace_dir = os.path.join(Config.STORAGE_DIR, workspace_id)
    shutil.rmtree(workspace_dir, ignore_errors=True)

    db.session.delete(workspace)
    db.session.commit()

    return jsonify({"status": "deleted"}), 200


def _sse_event(payload):
    return f"data: {json.dumps(payload)}\n\n"


@workspace_bp.route("/workspace/<workspace_id>/events", methods=["GET"])
def stream_events(workspace_id):
    """Server-Sent Events stream covering two independent tracks:
      - "ingestion": queued -> extracting -> embedding -> ready/failed
        (gates chat availability).
      - "topics": pending -> generating -> ready/failed (gates the
        topics/flashcards sidebar; independent of ingestion failures).

    Replays each track's current state first (covers clients that connect
    after a stage already happened, e.g. LoadingPage for ingestion or
    WorkspacePage for topics), then forwards live updates published by the
    Celery task (see app/services/events.py) until both tracks have each
    reached a terminal stage. A client only interested in one track (e.g.
    LoadingPage only cares about "ingestion") simply closes its connection
    once it sees that track's terminal event."""
    # Ownership check happens here, before entering generate()'s streaming
    # closure — flask.g is only valid within this request context, and the
    # generator runs lazily once the response starts streaming.
    workspace = _get_owned_workspace(workspace_id)
    if workspace is None:
        return jsonify({"error": "Workspace not found"}), 404

    ingestion_stage = workspace.stage or workspace.status
    initial_events = [
        {"track": "ingestion", "stage": ingestion_stage, "message": workspace.stage_message, "error": workspace.error_message},
        {"track": "topics", "stage": workspace.topics_stage, "message": workspace.topics_message, "error": workspace.topics_error},
    ]

    def generate():
        terminal_tracks = set()
        for event in initial_events:
            yield _sse_event(event)
            if event["stage"] in TERMINAL_STAGES:
                terminal_tracks.add(event["track"])

        if len(terminal_tracks) == 2:
            return

        try:
            for payload in subscribe(workspace_id, poll_timeout=KEEPALIVE_SECONDS):
                if payload is None:
                    yield ": keepalive\n\n"
                    continue
                yield _sse_event(payload)
                if payload.get("stage") in TERMINAL_STAGES:
                    terminal_tracks.add(payload.get("track"))
                    if len(terminal_tracks) == 2:
                        break
        except GeneratorExit:
            raise
        except Exception:
            logger.exception("workspace %s: SSE stream error", workspace_id)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@workspace_bp.route("/workspace/<workspace_id>/topics", methods=["GET"])
def get_topics(workspace_id):
    """List the topics the LLM generated for this workspace once ingestion finished."""
    workspace = _get_owned_workspace(workspace_id)
    if workspace is None:
        return jsonify({"error": "Workspace not found"}), 404
    topics = Topic.query.filter_by(workspace_id=workspace_id).all()
    return jsonify([t.to_dict() for t in topics])
