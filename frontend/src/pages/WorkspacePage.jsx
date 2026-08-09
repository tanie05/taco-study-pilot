import { useEffect, useRef, useState } from "react";
import ChatWindow from "../components/ChatWindow";
import TopicSidebar from "../components/TopicSidebar";
import FlashcardModal from "../components/FlashcardModal";
import ConfirmDialog from "../components/ConfirmDialog";
import AddFilesModal from "../components/AddFilesModal";
import { addFiles, deleteWorkspace, getTopics, subscribeToWorkspaceEvents } from "../services/api";

export default function WorkspacePage({ workspaceId, onDeleted, onFilesAdded }) {
  const [topics, setTopics] = useState([]);
  const [topicsStage, setTopicsStage] = useState("pending"); // pending | generating | ready | failed
  const [topicsError, setTopicsError] = useState(null);
  const [activeTopic, setActiveTopic] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showAddFiles, setShowAddFiles] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const unsubscribeRef = useRef(null);

  useEffect(() => {
    // Topic generation runs independently of (and after) ingestion, so
    // this page tracks its own "topics" track rather than waiting for it
    // before chat becomes available (see LoadingPage, which only waits on
    // the "ingestion" track).
    unsubscribeRef.current = subscribeToWorkspaceEvents(workspaceId, {
      onEvent: (payload) => {
        const { track, stage, error } = payload;
        if (track !== "topics") return;

        setTopicsStage(stage);
        if (stage === "ready") {
          unsubscribeRef.current?.();
          getTopics(workspaceId).then(setTopics).catch(() => setTopics([]));
        } else if (stage === "failed") {
          unsubscribeRef.current?.();
          setTopicsError(error || "Couldn't generate topics.");
        }
      },
    });

    return () => unsubscribeRef.current?.();
  }, [workspaceId]);

  async function handleDelete() {
    setDeleting(true);
    try {
      await deleteWorkspace(workspaceId);
      onDeleted();
    } catch {
      setDeleting(false);
      setShowDeleteConfirm(false);
    }
  }

  async function handleAddFiles(files) {
    await addFiles(workspaceId, files);
    setShowAddFiles(false);
    onFilesAdded();
  }

  return (
    <div className="page workspace-page">
      <div className="workspace-header">
        <button onClick={() => setShowAddFiles(true)}>Add more files</button>
        <button className="btn-danger" onClick={() => setShowDeleteConfirm(true)}>
          Delete workspace
        </button>
      </div>

      <div className="workspace-layout">
        <ChatWindow workspaceId={workspaceId} />
        <TopicSidebar
          topics={topics}
          topicsStage={topicsStage}
          topicsError={topicsError}
          onSelectTopic={setActiveTopic}
        />
      </div>

      {activeTopic && (
        <FlashcardModal topic={activeTopic} onClose={() => setActiveTopic(null)} />
      )}

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
