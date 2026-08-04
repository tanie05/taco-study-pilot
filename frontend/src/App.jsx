import { useState } from "react";
import UploadPage from "./pages/UploadPage";
import LoadingPage from "./pages/LoadingPage";
import WorkspacePage from "./pages/WorkspacePage";
import "./App.css";

export default function App() {
  const [workspaceId, setWorkspaceId] = useState(null);
  const [stage, setStage] = useState("upload"); // upload | loading | ready | failed
  const [errorMessage, setErrorMessage] = useState(null);

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

  return <WorkspacePage workspaceId={workspaceId} />;
}
