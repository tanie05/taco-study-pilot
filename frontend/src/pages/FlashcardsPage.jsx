import { useEffect, useRef, useState } from "react";
import TopicSidebar from "../components/TopicSidebar";
import FlashcardViewer from "../components/FlashcardViewer";
import { getTopics, subscribeToWorkspaceEvents } from "../services/api";

// Full-page replacement for the old TopicSidebar (right panel) +
// FlashcardModal (overlay) pairing — same topics/flashcards behavior, now
// laid out as its own page reached via the sidebar's "Flashcards" nav item.
export default function FlashcardsPage({ workspaceId }) {
  const [topics, setTopics] = useState([]);
  const [topicsStage, setTopicsStage] = useState("pending");
  const [topicsError, setTopicsError] = useState(null);
  const [activeTopic, setActiveTopic] = useState(null);
  const unsubscribeRef = useRef(null);

  useEffect(() => {
    // The SSE stream replays the workspace's currently persisted "topics"
    // stage first (see backend/app/services/events.py), so if topics were
    // already generated in an earlier session we still get a "ready" event
    // right away and fetch them below — no separate initial fetch needed.
    unsubscribeRef.current = subscribeToWorkspaceEvents(workspaceId, {
      onEvent: (payload) => {
        const { track, stage, error } = payload;
        if (track !== "topics") return;

        setTopicsStage(stage);
        if (stage === "ready") {
          unsubscribeRef.current?.();
          getTopics(workspaceId)
            .then(setTopics)
            .catch(() => {
              setTopics([]);
              setTopicsError("Couldn't load topics.");
            });
        } else if (stage === "failed") {
          unsubscribeRef.current?.();
          setTopicsError(error || "Couldn't generate topics.");
        }
      },
    });

    return () => unsubscribeRef.current?.();
  }, [workspaceId]);

  return (
    <div className="flashcards-page">
      <TopicSidebar
        topics={topics}
        topicsStage={topicsStage}
        topicsError={topicsError}
        activeTopicId={activeTopic?.id}
        onSelectTopic={setActiveTopic}
      />
      <div className="flashcards-main">
        {activeTopic ? (
          // key={activeTopic.id} forces a full remount when the user picks
          // a different topic, so index/flipped reset — this list is now
          // always visible next to the viewer (it used to be a modal that
          // had to be closed before picking another topic), so this switch
          // can happen while a viewer is already showing.
          <FlashcardViewer key={activeTopic.id} topic={activeTopic} />
        ) : (
          <p className="muted flashcards-empty">Select a topic to see its flashcards.</p>
        )}
      </div>
    </div>
  );
}
