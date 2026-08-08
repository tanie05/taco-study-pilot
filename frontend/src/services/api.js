// Thin wrapper around the Flask backend API (backend/app/api/*.py).
import axios from "axios";

const baseURL = "http://127.0.0.1:5001";

const api = axios.create({ baseURL });

// Uploads PDFs and starts async ingestion; backend returns a workspace_id to
// subscribe to via subscribeToWorkspaceEvents.
export function uploadFiles(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  return api.post("/upload", formData).then((res) => res.data);
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
  const source = new EventSource(`${baseURL}/workspace/${workspaceId}/events`);

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
