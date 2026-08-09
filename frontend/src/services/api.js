// Thin wrapper around the Flask backend API (backend/app/api/*.py).
import axios from "axios";

// Must match the frontend's own origin's hostname (both "localhost", not
// mixed with "127.0.0.1") for the guest_id cookie (see
// backend/app/services/auth.py) to be treated as same-site by the browser.
const baseURL = "http://localhost:5001";

// withCredentials so the guest_id cookie is sent/received cross-origin
// (frontend on :5173, API on :5001) — paired with supports_credentials +
// an explicit origin in the backend's CORS config.
const api = axios.create({ baseURL, withCredentials: true });

// Uploads PDFs and starts async ingestion; backend returns a workspace_id to
// subscribe to via subscribeToWorkspaceEvents. Fails with 409 if the caller
// (guest) already owns a workspace — see addFiles/deleteWorkspace.
export function uploadFiles(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  return api.post("/upload", formData).then((res) => res.data);
}

// Adds more PDFs to an existing workspace (same topic) and re-runs the
// whole pipeline (topics are regenerated from the combined content).
export function addFiles(workspaceId, files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  return api.post(`/workspace/${workspaceId}/files`, formData).then((res) => res.data);
}

// Returns the caller's single workspace, if any (404 otherwise) — used on
// app load to restore state across reloads via the guest_id cookie.
export function getMyWorkspace() {
  return api.get("/workspace/mine").then((res) => res.data);
}

// Permanently deletes a workspace and everything tied to it.
export function deleteWorkspace(workspaceId) {
  return api.delete(`/workspace/${workspaceId}`).then((res) => res.data);
}

// One-off status check. Prefer subscribeToWorkspaceEvents for live updates
// while a workspace's status is "processing".
export function getWorkspaceStatus(workspaceId) {
  return api.get(`/workspace/${workspaceId}/status`).then((res) => res.data);
}

// Streams ingestion progress via SSE instead of polling getWorkspaceStatus
// in a loop. Each event payload looks like:
//   { stage: "extracting" | "embedding" | "generating_topics" | "ready" | "failed",
//     message: string | null, error: string | null }
// Returns an unsubscribe function that closes the underlying connection.
export function subscribeToWorkspaceEvents(workspaceId, { onEvent, onError }) {
  // withCredentials so the SSE connection also carries the guest_id cookie.
  const source = new EventSource(`${baseURL}/workspace/${workspaceId}/events`, {
    withCredentials: true,
  });

  source.onmessage = (event) => {
    try {
      onEvent(JSON.parse(event.data));
    } catch {
      // Malformed payload; ignore and wait for the next event.
    }
  };

  source.onerror = (event) => {
    onError?.(event);
  };

  return () => source.close();
}

// Available once the workspace is "ready".
export function getTopics(workspaceId) {
  return api.get(`/workspace/${workspaceId}/topics`).then((res) => res.data);
}

// RAG chat: answers are grounded in the workspace's uploaded documents.
export function sendChatMessage(workspaceId, message) {
  return api
    .post("/chat", { workspace_id: workspaceId, message })
    .then((res) => res.data);
}

// Generates flashcards for a topic on demand (not precomputed).
export function generateFlashcards(topicId) {
  return api.post(`/topics/${topicId}/generate`).then((res) => res.data);
}
