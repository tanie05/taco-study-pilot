import { useEffect, useRef, useState } from "react";
import ChatWindow from "../components/ChatWindow";
import TopicSidebar from "../components/TopicSidebar";
import FlashcardModal from "../components/FlashcardModal";
import { getTopics, subscribeToWorkspaceEvents } from "../services/api";

export default function WorkspacePage({ workspaceId }) {
  const [topics, setTopics] = useState([]);
  const [topicsStage, setTopicsStage] = useState("pending"); // pending | generating | ready | failed
  const [topicsError, setTopicsError] = useState(null);
  const [activeTopic, setActiveTopic] = useState(null);
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

  return (
    <div className="page workspace-page">
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
    </div>
  );
}
