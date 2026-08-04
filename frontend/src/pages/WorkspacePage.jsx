import { useEffect, useState } from "react";
import ChatWindow from "../components/ChatWindow";
import TopicSidebar from "../components/TopicSidebar";
import FlashcardModal from "../components/FlashcardModal";
import { getTopics } from "../services/api";

export default function WorkspacePage({ workspaceId }) {
  const [topics, setTopics] = useState([]);
  const [activeTopic, setActiveTopic] = useState(null);

  useEffect(() => {
    getTopics(workspaceId).then(setTopics).catch(() => setTopics([]));
  }, [workspaceId]);

  return (
    <div className="page workspace-page">
      <div className="workspace-layout">
        <ChatWindow workspaceId={workspaceId} />
        <TopicSidebar topics={topics} onSelectTopic={setActiveTopic} />
      </div>

      {activeTopic && (
        <FlashcardModal topic={activeTopic} onClose={() => setActiveTopic(null)} />
      )}
    </div>
  );
}
