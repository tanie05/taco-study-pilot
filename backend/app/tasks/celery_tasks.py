import logging

from app.celery_app import celery_app
from app.extensions import db
from app.models import ResourceFile, Topic, Workspace
from app.services.events import publish_stage
from app.services.ingestion import chunk_text, embed_and_store, extract_text
from app.services.topics import generate_topics

logger = logging.getLogger(__name__)


def _set_ingestion_stage(workspace, stage, message=None, error=None):
    """Persist the ingestion-track stage (gates chat availability) and
    publish it over Redis pub/sub (live push to clients streaming
    GET /workspace/<id>/events)."""
    workspace.stage = stage
    workspace.stage_message = message
    db.session.commit()
    publish_stage(workspace.id, "ingestion", stage, message=message, error=error)


def _set_topics_stage(workspace, stage, message=None, error=None):
    """Persist the topics-track stage. Independent of the ingestion track
    above — a topics failure never touches workspace.status/stage, so chat
    stays usable even if topic generation fails."""
    workspace.topics_stage = stage
    workspace.topics_message = message
    workspace.topics_error = error
    db.session.commit()
    publish_stage(workspace.id, "topics", stage, message=message, error=error)


@celery_app.task(name="process_workspace")
def process_workspace(workspace_id):
    """Background job triggered by POST /upload. Runs two independent
    phases:
      1. Ingestion — extract text from each PDF, chunk + embed it into
         Qdrant. Success unlocks chat; failure marks the whole workspace
         "failed" and skips phase 2 (nothing to generate topics from).
      2. Topic generation — sampled from the ingested chunks. Tracked
         separately (topics_stage) so a failure here doesn't take chat
         away; it only affects the topics/flashcards sidebar.
    """
    from app import create_app

    # Worker runs in its own process, so it needs its own Flask/DB app context.
    app = create_app()
    with app.app_context():
        workspace = db.session.get(Workspace, workspace_id)
        if workspace is None:
            logger.warning("process_workspace: workspace %s not found", workspace_id)
            return

        logger.info("process_workspace: starting ingestion for workspace %s", workspace_id)

        try:
            files = ResourceFile.query.filter_by(workspace_id=workspace_id).all()
            _set_ingestion_stage(workspace, "extracting", f"Reading {len(files)} file(s)...")
            logger.info("workspace %s: extracting text from %d file(s)", workspace_id, len(files))

            all_chunks = []
            for f in files:
                text = extract_text(f.storage_path)
                chunks = chunk_text(text)
                logger.info(
                    "workspace %s: %s -> %d chunk(s)", workspace_id, f.filename, len(chunks)
                )
                all_chunks.extend((c, f.filename) for c in chunks)

            if not all_chunks:
                raise ValueError("No extractable text found in uploaded files")

            _set_ingestion_stage(workspace, "embedding", f"Embedding {len(all_chunks)} chunk(s)...")
            logger.info(
                "workspace %s: embedding and storing %d chunk(s) total",
                workspace_id,
                len(all_chunks),
            )
            embed_and_store(workspace_id, all_chunks)

            workspace.status = "ready"
            db.session.commit()
            _set_ingestion_stage(workspace, "ready")
            logger.info("workspace %s: ingestion complete, status=ready (chat unlocked)", workspace_id)

        except Exception as exc:
            logger.exception("workspace %s: ingestion failed", workspace_id)
            workspace.status = "failed"
            workspace.error_message = str(exc)
            db.session.commit()
            _set_ingestion_stage(workspace, "failed", error=str(exc))
            return  # nothing to generate topics from — skip phase 2 entirely

        try:
            _set_topics_stage(workspace, "generating", "Generating study topics...")
            # Only sample the first 20 chunks for topic generation to keep
            # the prompt short; full content is still searchable via chat.
            sample = [c for c, _ in all_chunks[:20]]
            topic_titles = generate_topics(workspace_id, sample)
            logger.info(
                "workspace %s: generated %d topic(s): %s",
                workspace_id,
                len(topic_titles),
                topic_titles,
            )
            for title in topic_titles:
                db.session.add(Topic(workspace_id=workspace_id, title=title))
            db.session.commit()
            _set_topics_stage(workspace, "ready")

        except Exception as exc:
            logger.exception("workspace %s: topic generation failed", workspace_id)
            db.session.rollback()
            _set_topics_stage(workspace, "failed", error=str(exc))
