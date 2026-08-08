# Celery instance used to run PDF ingestion in the background so the
# /upload request can return immediately (see app/tasks/celery_tasks.py).
import logging
import os
import sys

# Celery's `-A app.celery_app` resolution puts the backend dir on sys.path
# only *transiently* while it loads this module, then pops it back off —
# so a later, lazily-triggered import (e.g. from the worker_ready signal
# below) can't find sibling top-level packages like `scripts`. Put it back
# permanently so imports here behave the same as everywhere else.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery
from celery.signals import worker_ready

from config import Config

celery_app = Celery(
    "study_assistance",
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL,
    include=["app.tasks.celery_tasks"],
)

celery_app.conf.update(task_track_started=True)

logger = logging.getLogger(__name__)


@worker_ready.connect
def _log_startup_checks(**kwargs):
    """Runs once when the worker comes online (not per-task) so a down
    Qdrant/Ollama is a loud warning here instead of a task that silently
    hangs later. Skips the Celery-worker-ping check — this *is* the worker."""
    from scripts.check_services import CHECKS

    failed = []
    for name, check in CHECKS:
        if name == "Celery worker":
            continue
        ok, detail = check()
        (logger.info if ok else logger.warning)("[startup check] %s: %s — %s", name, "OK" if ok else "NOT OK", detail)
        if not ok:
            failed.append(name)

    if failed:
        logger.warning(
            "Worker started but %d dependenc%s down: %s. Ingestion tasks will fail or hang "
            "until these are fixed.",
            len(failed),
            "y is" if len(failed) == 1 else "ies are",
            ", ".join(failed),
        )
