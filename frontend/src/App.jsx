import { useEffect, useState } from "react";
import UploadPage from "./pages/UploadPage";
import LoadingPage from "./pages/LoadingPage";
import WorkspacePage from "./pages/WorkspacePage";
import { getMyWorkspace } from "./services/api";
import "./App.css";

export default function App() {
  const [workspaceId, setWorkspaceId] = useState(null);
  const [stage, setStage] = useState("checking"); // checking | upload | loading | ready | failed
  const [errorMessage, setErrorMessage] = useState(null);

  // The guest_id cookie (see backend/app/services/auth.py) lets the
  // backend recognize a returning guest's workspace, so on load we check
  // for one instead of always starting at the upload screen.
  useEffect(() => {
    getMyWorkspace()
      .then((workspace) => {
        setWorkspaceId(workspace.id);
        if (workspace.status === "processing") {
          setStage("loading");
        } else if (workspace.status === "ready") {
          setStage("ready");
        } else if (workspace.status === "failed") {
          setErrorMessage(workspace.error_message);
          setStage("failed");
        } else {
          setStage("upload");
        }
      })
      .catch(() => setStage("upload"));
  }, []);

  if (stage === "checking") {
    return (
      <div className="page loading-page">
        <div className="spinner" />
      </div>
    );
  }

  if (stage === "upload") {
    return (
      <UploadPage
        onUploaded={(id) => {
          setWorkspaceId(id);
          setStage("loading");
        }}
      />
    );
  }

  if (stage === "loading") {
    return (
      <LoadingPage
        workspaceId={workspaceId}
        onReady={() => setStage("ready")}
        onFailed={(msg) => {
          setErrorMessage(msg);
          setStage("failed");
        }}
      />
    );
  }

  if (stage === "failed") {
    return (
      <div className="page">
        <h2>Something went wrong</h2>
        <p className="error">{errorMessage}</p>
        <button onClick={() => setStage("upload")}>Try again</button>
      </div>
    );
  }

  return (
    <WorkspacePage
      workspaceId={workspaceId}
      onDeleted={() => {
        setWorkspaceId(null);
        setStage("upload");
      }}
      onFilesAdded={() => setStage("loading")}
    />
  );
}
