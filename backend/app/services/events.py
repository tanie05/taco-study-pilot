"""Redis pub/sub used to push live ingestion-progress updates from the
Celery worker to any client streaming GET /workspace/<id>/events.

Redis is already running as the Celery broker/result backend (see
app/celery_app.py), so we reuse that same instance rather than adding a new
dependency. Pub/sub is a live-push convenience layer only — the Workspace
row's `stage`/`stage_message` columns (updated by the caller alongside these
publishes) remain the source of truth for clients that connect late.
"""
import json
import logging

import redis

from config import Config

logger = logging.getLogger(__name__)

_redis_client = None


def _get_client():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(Config.REDIS_URL)
    return _redis_client


def _channel(workspace_id):
    return f"workspace:{workspace_id}:events"


def publish_stage(workspace_id, track, stage, message=None, error=None):
    """Publish a stage update for workspace_id on the given track
    ("ingestion" or "topics" — see app/tasks/celery_tasks.py). Never
    raises — a Redis hiccup shouldn't fail ingestion, since the DB stage
    columns are still updated by the caller regardless."""
    payload = {"track": track, "stage": stage, "message": message, "error": error}
    try:
        _get_client().publish(_channel(workspace_id), json.dumps(payload))
    except Exception:
        logger.exception(
            "events: failed to publish %s stage %r for workspace %s", track, stage, workspace_id
        )


def subscribe(workspace_id, poll_timeout=15):
    """Yield parsed JSON stage-update messages for workspace_id as they
    arrive, or None every `poll_timeout` seconds if nothing arrived (so the
    caller can emit an SSE keepalive instead of blocking forever). The
    caller is expected to iterate this from within a streaming response."""
    pubsub = _get_client().pubsub()
    pubsub.subscribe(_channel(workspace_id))
    try:
        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True, timeout=poll_timeout)
            if message is None:
                yield None
                continue
            try:
                yield json.loads(message["data"])
            except (TypeError, ValueError):
                logger.warning("events: dropping malformed message on %s: %r", _channel(workspace_id), message["data"])
    finally:
        pubsub.close()
