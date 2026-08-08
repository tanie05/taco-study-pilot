import { useEffect, useRef, useState } from "react";
import { subscribeToWorkspaceEvents } from "../services/api";

// Friendly fallback text per stage, used when the backend event doesn't
// include its own `message` (e.g. workspaces created before stage_message
// existed).
const STAGE_MESSAGES = {
  queued: "Getting ready...",
  extracting: "Reading your files...",
  embedding: "Indexing your content...",
  generating_topics: "Building your study topics...",
};

export default function LoadingPage({ workspaceId, onReady, onFailed }) {
  const [message, setMessage] = useState("Ingestion in progress...");
  const unsubscribeRef = useRef(null);

  useEffect(() => {
    unsubscribeRef.current = subscribeToWorkspaceEvents(workspaceId, {
      onEvent: (payload) => {
        const { track, stage, message: stageMessage, error } = payload;
        // This page only cares about ingestion (chat unlocks as soon as
        // it's ready); topic generation is tracked separately once the
        // user reaches WorkspacePage.
        if (track !== "ingestion") return;

        if (stage === "ready") {
          unsubscribeRef.current?.();
          onReady();
          return;
        }
        if (stage === "failed") {
          unsubscribeRef.current?.();
          onFailed(error || "Ingestion failed.");
          return;
        }

        setMessage(stageMessage || STAGE_MESSAGES[stage] || "Ingestion in progress...");
      },
      onError: () => {
        // EventSource retries the connection automatically; just reflect
        // the hiccup in the UI while it does.
        setMessage("Having trouble connecting, retrying...");
      },
    });

    return () => unsubscribeRef.current?.();
  }, [workspaceId, onReady, onFailed]);

  return (
    <div className="page loading-page">
      <div className="spinner" />
      <p>{message}</p>
    </div>
  );
}
