import os

from flask import Flask
from flask_cors import CORS

from config import Config
from app.extensions import db


def create_app():
    """Flask application factory. Also called from the Celery worker
    (see app/tasks/celery_tasks.py) to get a DB-bound app context."""
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

    return app
