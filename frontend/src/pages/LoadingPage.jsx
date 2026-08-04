import { useEffect, useRef, useState } from "react";
import { getWorkspaceStatus } from "../services/api";

export default function LoadingPage({ workspaceId, onReady, onFailed }) {
  const [message, setMessage] = useState("Ingestion in progress...");
  const pollRef = useRef(null);

  useEffect(() => {
    pollRef.current = setInterval(async () => {
      try {
        const data = await getWorkspaceStatus(workspaceId);
        if (data.status === "ready") {
          clearInterval(pollRef.current);
          onReady();
        } else if (data.status === "failed") {
          clearInterval(pollRef.current);
          onFailed(data.error_message || "Ingestion failed.");
        }
      } catch {
        setMessage("Having trouble checking status, retrying...");
      }
    }, 2000);

    return () => clearInterval(pollRef.current);
  }, [workspaceId, onReady, onFailed]);

  return (
    <div className="page loading-page">
      <div className="spinner" />
      <p>{message}</p>
    </div>
  );
}
