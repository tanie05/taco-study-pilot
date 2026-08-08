import logging

from app.celery_app import celery_app
from app.extensions import db
from app.models import ResourceFile, Topic, Workspace
from app.services.ingestion import chunk_text, embed_and_store, extract_text
from app.services.topics import generate_topics

logger = logging.getLogger(__name__)


@celery_app.task(name="process_workspace")
def process_workspace(workspace_id):
    """Background job triggered by POST /upload. Extracts text from each
    PDF, chunks + embeds it into Qdrant, and generates the workspace's
    topics — then flips the workspace status to "ready" (or "failed")."""
    from app import create_app

    # Worker runs in its own process, so it needs its own Flask/DB app context.
    logger.info("here ")
    app = create_app()
    with app.app_context():
        workspace = db.session.get(Workspace, workspace_id)
        if workspace is None:
            logger.warning("process_workspace: workspace %s not found", workspace_id)
            return

        logger.info("process_workspace: starting ingestion for workspace %s", workspace_id)

        try:
            files = ResourceFile.query.filter_by(workspace_id=workspace_id).all()
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

            logger.info(
                "workspace %s: embedding and storing %d chunk(s) total",
                workspace_id,
                len(all_chunks),
            )
            embed_and_store(workspace_id, all_chunks)

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

            workspace.status = "ready"
            db.session.commit()
            logger.info("workspace %s: ingestion complete, status=ready", workspace_id)

        except Exception as exc:
            logger.exception("workspace %s: ingestion failed", workspace_id)
            workspace.status = "failed"
            workspace.error_message = str(exc)
            db.session.commit()
