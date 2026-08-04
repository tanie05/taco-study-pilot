from app.celery_app import celery_app
from app.extensions import db
from app.models import ResourceFile, Topic, Workspace
from app.services.ingestion import chunk_text, embed_and_store, extract_text
from app.services.topics import generate_topics


@celery_app.task(name="process_workspace")
def process_workspace(workspace_id):
    """Background job triggered by POST /upload. Extracts text from each
    PDF, chunks + embeds it into Qdrant, and generates the workspace's
    topics — then flips the workspace status to "ready" (or "failed")."""
    from app import create_app

    # Worker runs in its own process, so it needs its own Flask/DB app context.
    app = create_app()
    with app.app_context():
        workspace = db.session.get(Workspace, workspace_id)
        if workspace is None:
            return

        try:
            files = ResourceFile.query.filter_by(workspace_id=workspace_id).all()

            all_chunks = []
            for f in files:
                text = extract_text(f.storage_path)
                chunks = chunk_text(text)
                all_chunks.extend((c, f.filename) for c in chunks)

            if not all_chunks:
                raise ValueError("No extractable text found in uploaded files")

            embed_and_store(workspace_id, all_chunks)

            # Only sample the first 20 chunks for topic generation to keep
            # the prompt short; full content is still searchable via chat.
            sample = [c for c, _ in all_chunks[:20]]
            topic_titles = generate_topics(workspace_id, sample)
            for title in topic_titles:
                db.session.add(Topic(workspace_id=workspace_id, title=title))

            workspace.status = "ready"
            db.session.commit()

        except Exception as exc:
            workspace.status = "failed"
            workspace.error_message = str(exc)
            db.session.commit()
