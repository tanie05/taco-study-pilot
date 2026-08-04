// Thin wrapper around the Flask backend API (backend/app/api/*.py).
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:5001",
});

// Uploads PDFs and starts async ingestion; backend returns a workspace_id to poll.
export function uploadFiles(files) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }
  return api.post("/upload", formData).then((res) => res.data);
}

// Poll this while a workspace's status is "processing".
export function getWorkspaceStatus(workspaceId) {
  return api.get(`/workspace/${workspaceId}/status`).then((res) => res.data);
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
