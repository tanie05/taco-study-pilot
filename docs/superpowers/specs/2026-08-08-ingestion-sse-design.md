# Ingestion Progress via SSE (replacing polling)

## Problem

The frontend currently polls `GET /workspace/<id>/status` every 2s
(`frontend/src/pages/LoadingPage.jsx`) while the Celery task
`process_workspace` (`backend/app/tasks/celery_tasks.py`) runs PDF text
extraction, embedding, and topic generation. This only exposes the final
`processing`/`ready`/`failed` status, adds constant request overhead, and has
up to ~2s of latency on the ready/failed transition.

## Goals

- Replace polling with a Server-Sent Events (SSE) stream pushed from the
  backend.
- Along the way, expose intermediate ingestion stages (extracting → embedding
  → generating topics → ready/failed) for a richer loading UI, not just the
  terminal status.

## Non-goals

- No WebSockets, no bidirectional communication — ingestion progress is
  one-directional (server → client).
- No change to the ingestion pipeline's actual work (extraction, embedding,
  topic generation logic in `app/services/ingestion.py` /
  `app/services/topics.py` is unchanged).
- No fallback-to-polling logic — EventSource's built-in reconnection covers
  transient connection drops.

## Architecture

### Push mechanism: Redis pub/sub

Redis is already running as the Celery broker/result backend
(`Config.REDIS_URL`). We reuse it for pub/sub so the Celery worker (a
separate process from the Flask API) can push stage updates to any client
currently streaming `/workspace/<id>/events`.

New module `backend/app/services/events.py`:

- `publish_stage(workspace_id, stage, message=None, error=None)` — publishes
  a JSON payload (`{"stage": ..., "message": ..., "error": ...}`) to Redis
  channel `workspace:{workspace_id}:events`. Publish failures are caught and
  logged, never raised — pub/sub is a live-push convenience layer, not the
  source of truth.
- `subscribe(workspace_id)` — returns a generator yielding parsed JSON
  messages from that channel, for the SSE view to consume.

### Persisted stage (source of truth)

`Workspace` model (`backend/app/models.py`) gains two columns:

- `stage` (string) — one of `queued`, `extracting`, `embedding`,
  `generating_topics`, `ready`, `failed`.
- `stage_message` (text, nullable) — human-readable detail, e.g.
  `"Embedding 42 chunks..."`.

`process_workspace` updates `workspace.stage` / `stage_message` in the DB
*and* calls `publish_stage(...)` at each transition:

`queued → extracting → embedding → generating_topics → ready` (or `failed`
with an error message, same as today's `error_message` column).

Persisting stage server-side means a client that connects after a stage has
already happened (page refresh mid-ingestion, or ingestion already finished
before the client ever opened a stream) still sees correct current state —
it doesn't depend on catching a live pub/sub message.

### SSE endpoint

`GET /workspace/<id>/events` in `backend/app/api/workspace.py`, returning a
`text/event-stream` streaming response:

1. Read `workspace.stage` (falling back to `workspace.status` if `stage` is
   unset, for workspaces created before this change) and immediately emit it
   as the first SSE `data:` event.
2. If that stage is already terminal (`ready` / `failed`), close the stream.
3. Otherwise, subscribe to the Redis channel for this workspace and forward
   each message as an SSE event, until a `ready` or `failed` stage is
   forwarded (then close).
4. Emit a `: keepalive\n\n` comment line every ~15s of inactivity so the
   connection isn't dropped as idle by browsers/proxies.

The Flask dev server (`backend/run.py`) must run with `threaded=True` so it
can hold open SSE connections while still serving other requests
concurrently.

The existing `GET /workspace/<id>/status` endpoint is unchanged — still
useful for one-off status checks — it's just no longer polled in a loop.

## Frontend

- `frontend/src/services/api.js`: add
  `subscribeToWorkspaceEvents(workspaceId, { onEvent, onError })` that opens
  an `EventSource` against `/workspace/<id>/events`, JSON-parses
  `event.data`, and calls `onEvent(payload)`; wires `EventSource.onerror` to
  `onError`.
- `frontend/src/pages/LoadingPage.jsx`: replace the `setInterval` +
  `getWorkspaceStatus` polling loop with this subscription.
  - On each event, update the displayed message from `payload.message`,
    falling back to a friendly default per `payload.stage` (e.g.
    `extracting → "Reading your files..."`, `embedding → "Indexing your
    content..."`, `generating_topics → "Building your study topics..."`) if
    the worker didn't send one.
  - `stage === "ready"` → close the EventSource, call `onReady()`.
  - `stage === "failed"` → close the EventSource, call
    `onFailed(payload.error || "Ingestion failed.")`.
  - `EventSource.onerror` → show "Having trouble connecting, retrying..."
    and let the browser's built-in auto-reconnect handle retry (no manual
    retry loop).

## Error handling & edge cases

- Redis publish failures in the Celery task are logged, not raised —
  ingestion continues; the DB `stage` column remains the source of truth for
  any client that reconnects.
- If the SSE endpoint's Redis subscription drops (e.g. Redis restart), the
  generator ends the stream; the browser's `EventSource` auto-reconnects,
  and step 1 of the endpoint (replay current DB stage) means no progress
  information is lost on reconnect.
- CORS: `flask-cors` is already applied app-wide (`app/__init__.py`), no
  extra configuration needed for `text/event-stream` responses.

## Testing

- Manual: upload PDFs, confirm in the Network tab a single persistent
  `/workspace/<id>/events` connection replaces the repeated `/status` polls,
  and that stage messages update live as ingestion proceeds.
  Verify `ready`/`failed` terminate the stream and route correctly.
- Manual: kill the Celery worker mid-ingestion, confirm the frontend shows
  the reconnect/retry message instead of hanging silently with no feedback.
- Manual: refresh the loading page mid-ingestion, confirm it immediately
  shows the current stage rather than a blank/default message.
