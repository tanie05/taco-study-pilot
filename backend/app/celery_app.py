# Celery instance used to run PDF ingestion in the background so the
# /upload request can return immediately (see app/tasks/celery_tasks.py).
from celery import Celery

from config import Config

celery_app = Celery(
    "study_assistance",
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL,
    include=["app.tasks.celery_tasks"],
)

celery_app.conf.update(task_track_started=True)
