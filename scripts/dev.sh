#!/usr/bin/env bash
# One-command dev launcher: brings up every dependency ingestion needs
# (Redis, Qdrant, Ollama, Celery worker) plus the Flask API, so a missing
# piece is a startup error, not a silently stuck upload.
#
# Usage: ./scripts/dev.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
PIDS=()

cleanup() {
    echo ""
    echo "Shutting down..."
    for pid in "${PIDS[@]:-}"; do
        kill "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT INT TERM

echo "==> Redis + Qdrant (docker compose)"
(cd "$REPO_ROOT" && docker compose up -d)

echo "==> Ollama"
if curl -s -m 2 http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "    already running"
else
    ollama serve > /tmp/ollama-dev.log 2>&1 &
    PIDS+=($!)
    echo "    started (logs: /tmp/ollama-dev.log)"
fi

VENV_BIN="$REPO_ROOT/.venv/bin"

echo "==> Celery worker"
(cd "$BACKEND_DIR" && "$VENV_BIN/celery" -A app.celery_app worker --loglevel=info) &
PIDS+=($!)

sleep 5  # give the worker time to finish mingling before Flask's startup check pings it

echo "==> Flask API (http://localhost:5001)"
(cd "$BACKEND_DIR" && "$VENV_BIN/python" run.py) &
PIDS+=($!)

wait
