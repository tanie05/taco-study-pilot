import json
import logging

from flask import Blueprint, Response, jsonify

from app.extensions import db
from app.models import Topic, Workspace
from app.services.events import subscribe

workspace_bp = Blueprint("workspace", __name__)

logger = logging.getLogger(__name__)

TERMINAL_STAGES = {"ready", "failed"}
KEEPALIVE_SECONDS = 15


@workspace_bp.route("/workspace/<workspace_id>/status", methods=["GET"])
def get_status(workspace_id):
    """One-off status check (status: processing -> ready or failed). The
    frontend now uses GET /workspace/<id>/events for live updates instead
    of polling this in a loop."""
    workspace = db.session.get(Workspace, workspace_id)
    if workspace is None:
        return jsonify({"error": "Workspace not found"}), 404
    return jsonify(workspace.to_dict())


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
    workspace = db.session.get(Workspace, workspace_id)
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
    workspace = db.session.get(Workspace, workspace_id)
    if workspace is None:
        return jsonify({"error": "Workspace not found"}), 404
    topics = Topic.query.filter_by(workspace_id=workspace_id).all()
    return jsonify([t.to_dict() for t in topics])
