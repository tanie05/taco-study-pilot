import uuid
from datetime import datetime

from app.extensions import db


def gen_uuid():
    return str(uuid.uuid4())


class Workspace(db.Model):
    """One upload session: a set of PDFs plus the topics generated from them.
    status moves processing -> ready (or failed) as the Celery task runs."""

    __tablename__ = "workspaces"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    status = db.Column(db.String(20), nullable=False, default="processing")
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    files = db.relationship("ResourceFile", backref="workspace", cascade="all, delete-orphan")
    topics = db.relationship("Topic", backref="workspace", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
        }


class ResourceFile(db.Model):
    """A single uploaded PDF belonging to a workspace; storage_path points
    into Config.STORAGE_DIR on disk."""

    __tablename__ = "resource_files"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    workspace_id = db.Column(db.String(36), db.ForeignKey("workspaces.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    storage_path = db.Column(db.String(500), nullable=False)


class Topic(db.Model):
    """An LLM-generated study topic for a workspace. Flashcards are generated
    on demand from a topic (see app/services/topics.py) and cached in the
    flashcards table so repeat requests don't hit the LLM again."""

    __tablename__ = "topics"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    workspace_id = db.Column(db.String(36), db.ForeignKey("workspaces.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)

    flashcards = db.relationship("Flashcard", backref="topic", cascade="all, delete-orphan")

    def to_dict(self):
        return {"id": self.id, "title": self.title}


class Flashcard(db.Model):
    """A single question/answer flashcard generated for a topic."""

    __tablename__ = "flashcards"

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    topic_id = db.Column(db.String(36), db.ForeignKey("topics.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)

    def to_dict(self):
        return {"question": self.question, "answer": self.answer}
