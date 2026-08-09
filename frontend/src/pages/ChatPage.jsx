import { useEffect, useRef, useState } from "react";
import UploadDropzone from "../components/UploadDropzone";
import ChatWindow from "../components/ChatWindow";
import { uploadFiles, subscribeToWorkspaceEvents } from "../services/api";

// Friendly fallback text per stage, used when the backend event doesn't
// include its own `message` (e.g. workspaces created before stage_message
// existed).
const STAGE_MESSAGES = {
  queued: "Getting ready...",
  extracting: "Reading your files...",
  embedding: "Indexing your content...",
  generating_topics: "Building your study topics...",
};

// Merges the old UploadPage + LoadingPage + WorkspacePage's chat view into
// one page, driven entirely by the `stage` state App.jsx already tracks.
export default function ChatPage({ stage, workspaceId, errorMessage, onUploaded, onReady, onFailed, onRetry }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [loadingMessage, setLoadingMessage] = useState("Ingestion in progress...");
  const unsubscribeRef = useRef(null);

  useEffect(() => {
    if (stage !== "loading" || !workspaceId) return;

    // This page only cares about the "ingestion" track (chat unlocks as
    // soon as it's ready); topic generation is tracked separately by
    // FlashcardsPage once the user navigates there.
    unsubscribeRef.current = subscribeToWorkspaceEvents(workspaceId, {
      onEvent: (payload) => {
        const { track, stage: eventStage, message, error } = payload;
        if (track !== "ingestion") return;

        if (eventStage === "ready") {
          unsubscribeRef.current?.();
          onReady();
          return;
        }
        if (eventStage === "failed") {
          unsubscribeRef.current?.();
          onFailed(error || "Ingestion failed.");
          return;
        }
        setLoadingMessage(message || STAGE_MESSAGES[eventStage] || "Ingestion in progress...");
      },
      onError: () => setLoadingMessage("Having trouble connecting, retrying..."),
    });

    return () => unsubscribeRef.current?.();
  }, [stage, workspaceId, onReady, onFailed]);

  async function handleUpload() {
    setUploading(true);
    setUploadError(null);
    try {
      const { workspace_id } = await uploadFiles(selectedFiles);
      onUploaded(workspace_id, selectedFiles.length);
    } catch (err) {
      setUploadError(err.response?.data?.error || "Upload failed. Please try again.");
      setUploading(false);
    }
  }

  if (stage === "checking") {
    return (
      <div className="chat-page chat-page-centered">
        <div className="spinner" />
      </div>
    );
  }

  if (stage === "upload") {
    return (
      <div className="chat-page chat-page-centered">
        <p className="greet">Hi, I am taco, your AI study assistant</p>
        <h1 className="headline">
          Upload study materials and
          <br />
          I'll help with the prep
        </h1>

        <div className="input-card">
          <UploadDropzone onFilesSelected={setSelectedFiles} />

          {selectedFiles.length > 0 && (
            <ul className="file-list">
              {selectedFiles.map((f) => (
                <li key={f.name}>{f.name}</li>
              ))}
            </ul>
          )}

          {uploadError && <p className="error">{uploadError}</p>}

          <button disabled={selectedFiles.length === 0 || uploading} onClick={handleUpload}>
            {uploading ? "Uploading..." : "Upload & Start"}
          </button>
        </div>
      </div>
    );
  }

  if (stage === "loading") {
    return (
      <div className="chat-page chat-page-centered">
        <div className="spinner" />
        <p>{loadingMessage}</p>
      </div>
    );
  }

  if (stage === "failed") {
    return (
      <div className="chat-page chat-page-centered">
        <h2>Something went wrong</h2>
        <p className="error">{errorMessage}</p>
        <button onClick={onRetry}>Try again</button>
      </div>
    );
  }

  return (
    <div className="chat-page">
      <div className="chat-header">Study Assistant</div>
      <ChatWindow workspaceId={workspaceId} />
    </div>
  );
}
