"""Preflight check for everything ingestion depends on.

Run standalone any time something feels stuck:

    python scripts/check_services.py

Also imported by app/__init__.py (on API startup) and app/celery_app.py
(on worker startup) so the gap that caused ingestion to silently hang
forever — no Celery worker running, or Ollama down — is surfaced
immediately as a loud warning instead of a task that never finishes.
"""

import logging
import os
import sys

# Let this run standalone as `python scripts/check_services.py` regardless
# of cwd, by putting the backend root (this file's parent's parent) on the
# path so `from config import Config` resolves the same way it does when
# imported from app/__init__.py or app/celery_app.py.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import redis
import requests

from config import Config

logger = logging.getLogger(__name__)


def check_redis():
    try:
        redis.Redis.from_url(Config.REDIS_URL, socket_connect_timeout=2).ping()
        return True, f"reachable at {Config.REDIS_URL}"
    except Exception as exc:
        return False, f"unreachable at {Config.REDIS_URL} ({exc})"


def check_qdrant():
    try:
        resp = requests.get(f"{Config.QDRANT_URL}/collections", timeout=2)
        resp.raise_for_status()
        return True, f"reachable at {Config.QDRANT_URL}"
    except Exception as exc:
        return False, f"unreachable at {Config.QDRANT_URL} ({exc})"


def check_ollama():
    try:
        resp = requests.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=2)
        resp.raise_for_status()
        models = {m["model"] for m in resp.json().get("models", [])}
        if Config.OLLAMA_MODEL not in models and f"{Config.OLLAMA_MODEL}:latest" not in models:
            return False, (
                f"reachable at {Config.OLLAMA_BASE_URL} but model '{Config.OLLAMA_MODEL}' "
                f"isn't pulled — run `ollama pull {Config.OLLAMA_MODEL}`"
            )
        return True, f"reachable at {Config.OLLAMA_BASE_URL}, model '{Config.OLLAMA_MODEL}' present"
    except Exception as exc:
        return False, (
            f"unreachable at {Config.OLLAMA_BASE_URL} ({exc}) — run `ollama serve`"
        )


def check_celery_worker():
    try:
        from app.celery_app import celery_app

        replies = celery_app.control.inspect(timeout=2).ping() or {}
        if replies:
            return True, f"{len(replies)} worker(s) online: {', '.join(replies)}"
        return False, "no worker responded — run `celery -A app.celery_app worker --loglevel=info`"
    except Exception as exc:
        return False, f"could not reach a worker ({exc})"


CHECKS = [
    ("Redis (Celery broker)", check_redis),
    ("Qdrant (vector store)", check_qdrant),
    ("Ollama (local LLM)", check_ollama),
    ("Celery worker", check_celery_worker),
]


def run_checks(log=logger.warning, log_ok=logger.info):
    """Runs all checks, logging one line per dependency. Returns the list
    of names that failed (empty list = everything healthy)."""
    failed = []
    for name, check in CHECKS:
        ok, detail = check()
        if ok:
            log_ok("[startup check] %s: OK — %s", name, detail)
        else:
            log("[startup check] %s: NOT OK — %s", name, detail)
            failed.append(name)
    return failed


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    failed = run_checks()
    if failed:
        print(f"\n{len(failed)} dependenc{'y is' if len(failed) == 1 else 'ies are'} down: "
              f"{', '.join(failed)}. Uploads will hang until these are fixed.")
        sys.exit(1)
    print("\nAll dependencies healthy.")
