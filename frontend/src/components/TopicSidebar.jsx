export default function TopicSidebar({ topics, topicsStage, topicsError, activeTopicId, onSelectTopic }) {
  return (
    <div className="topic-sidebar">
      <h3>Topics</h3>
      {(topicsStage === "pending" || topicsStage === "generating") && (
        <p className="muted">Generating study topics...</p>
      )}
      {topicsStage === "failed" && (
        <p className="error">{topicsError || "Couldn't generate topics."}</p>
      )}
      {topicsStage === "ready" && topicsError && <p className="error">{topicsError}</p>}
      {topicsStage === "ready" && !topicsError && topics.length === 0 && (
        <p className="muted">No topics found.</p>
      )}
      <ul>
        {topics.map((topic) => (
          <li key={topic.id}>
            <button
              className={`topic-button ${activeTopicId === topic.id ? "active" : ""}`}
              onClick={() => onSelectTopic(topic)}
            >
              {topic.title}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
