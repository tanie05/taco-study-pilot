import { useCallback, useEffect, useState } from "react";
import Sidebar from "./components/Sidebar";
import ChatPage from "./pages/ChatPage";
import FlashcardsPage from "./pages/FlashcardsPage";
import AddFilesModal from "./components/AddFilesModal";
import ConfirmDialog from "./components/ConfirmDialog";
import { addFiles, deleteWorkspace, getMyWorkspace } from "./services/api";
import "./App.css";

export default function App() {
  const [workspaceId, setWorkspaceId] = useState(null);
  const [stage, setStage] = useState("checking"); // checking | upload | loading | ready | failed
  const [errorMessage, setErrorMessage] = useState(null);
  const [fileCount, setFileCount] = useState(0);
  const [currentPage, setCurrentPage] = useState("chat"); // chat | flashcards
  const [showAddFiles, setShowAddFiles] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  // The guest_id cookie (see backend/app/services/auth.py) lets the
  // backend recognize a returning guest's workspace, so on load we check
  // for one instead of always starting at the upload screen.
  useEffect(() => {
    getMyWorkspace()
      .then((workspace) => {
        setWorkspaceId(workspace.id);
        setFileCount(workspace.file_count);
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

  function handleUploaded(id, count) {
    setWorkspaceId(id);
    setFileCount(count);
    setStage("loading");
    setCurrentPage("chat");
  }

  async function handleAddFiles(files) {
    await addFiles(workspaceId, files);
    setShowAddFiles(false);
    setStage("loading");
    setCurrentPage("chat");
  }

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteWorkspace(workspaceId);
      setWorkspaceId(null);
      setFileCount(0);
      setStage("upload");
      setCurrentPage("chat");
    } catch {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  }

  // Stable references: ChatPage's SSE-subscription effect depends on these
  // callbacks, so without useCallback a fresh closure on every App render
  // (e.g. from opening the Add Files / Delete Workspace dialogs) would
  // re-run that effect and needlessly tear down and reopen the EventSource
  // connection while ingestion is still in progress.
  const handleReady = useCallback(() => setStage("ready"), []);
  const handleFailed = useCallback((msg) => {
    setErrorMessage(msg);
    setStage("failed");
  }, []);
  const handleRetry = useCallback(() => setStage("upload"), []);

  const hasWorkspace = stage === "loading" || stage === "ready" || stage === "failed";
  const workspace = hasWorkspace
    ? { fileCount, status: stage === "loading" ? "processing" : stage }
    : null;
  const flashcardsEnabled = stage === "ready";

  return (
    <div className="app-shell">
      <Sidebar
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        workspace={workspace}
        flashcardsEnabled={flashcardsEnabled}
        onAddFiles={() => setShowAddFiles(true)}
        onDeleteWorkspace={() => setShowDeleteConfirm(true)}
      />

      <main className="app-main">
        {currentPage === "flashcards" && flashcardsEnabled ? (
          <FlashcardsPage workspaceId={workspaceId} />
        ) : (
          <ChatPage
            stage={stage}
            workspaceId={workspaceId}
            errorMessage={errorMessage}
            onUploaded={handleUploaded}
            onReady={handleReady}
            onFailed={handleFailed}
            onRetry={handleRetry}
          />
        )}
      </main>

      {showAddFiles && (
        <AddFilesModal onSubmit={handleAddFiles} onClose={() => setShowAddFiles(false)} />
      )}

      {showDeleteConfirm && (
        <ConfirmDialog
          title="Delete workspace?"
          message="This permanently deletes all files, topics, and flashcards in this workspace."
          confirmLabel="Delete"
          confirming={deleting}
          onCancel={() => setShowDeleteConfirm(false)}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
}
