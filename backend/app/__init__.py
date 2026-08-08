import logging
import os

from flask import Flask
from flask_cors import CORS

from config import Config
from app.extensions import db

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def _add_missing_columns():
    """db.create_all() only creates tables that don't exist yet — it won't
    add new columns to a table from an earlier version of the schema (and
    this project has no migration tool). Patch those in with a plain
    ALTER TABLE so existing SQLite files (e.g. instance/app.db) pick up new
    columns like Workspace.stage without needing to delete the DB."""
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    existing_columns = {col["name"] for col in inspector.get_columns("workspaces")}
    if "stage" not in existing_columns:
        db.session.execute(text("ALTER TABLE workspaces ADD COLUMN stage VARCHAR(30) DEFAULT 'queued'"))
    if "stage_message" not in existing_columns:
        db.session.execute(text("ALTER TABLE workspaces ADD COLUMN stage_message TEXT"))
    if "topics_stage" not in existing_columns:
        db.session.execute(text("ALTER TABLE workspaces ADD COLUMN topics_stage VARCHAR(20) DEFAULT 'pending'"))
    if "topics_message" not in existing_columns:
        db.session.execute(text("ALTER TABLE workspaces ADD COLUMN topics_message TEXT"))
    if "topics_error" not in existing_columns:
        db.session.execute(text("ALTER TABLE workspaces ADD COLUMN topics_error TEXT"))
    db.session.commit()


def create_app(run_checks=False):
    """Flask application factory. Also called from the Celery worker
    (see app/tasks/celery_tasks.py) to get a DB-bound app context.

    run_checks: log a preflight health check of Redis/Qdrant/Ollama/Celery
    on startup. Only enabled for the actual API server (run.py) — the
    Celery task also calls create_app() per-task, and re-running the
    check there would just add latency to every single task.
    """
    app = Flask(__name__)
    app.config.from_object(Config)

    # Make sure the folders for uploaded PDFs and the SQLite DB exist.
    os.makedirs(Config.STORAGE_DIR, exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "instance"), exist_ok=True)

    CORS(app)  # allow the Vite frontend (different origin) to call this API
    db.init_app(app)

    # Blueprints are the API route groups, one per feature area.
    from app.api.upload import upload_bp
    from app.api.workspace import workspace_bp
    from app.api.chat import chat_bp
    from app.api.topics import topics_bp

    app.register_blueprint(upload_bp)
    app.register_blueprint(workspace_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(topics_bp)

    with app.app_context():
        db.create_all()  # create tables on startup (no migrations in this project)
        _add_missing_columns()  # patch columns onto tables that already existed

    if run_checks:
        from scripts.check_services import run_checks as _run_checks

        failed = _run_checks()
        if failed:
            logging.warning(
                "Startup check found %d problem(s): %s. Uploads will hang until these "
                "are fixed — see `python scripts/check_services.py` for details.",
                len(failed),
                ", ".join(failed),
            )

    return app
