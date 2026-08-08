export default function TopicSidebar({ topics, topicsStage, topicsError, onSelectTopic }) {
  return (
    <div className="topic-sidebar">
      <h3>Flashcard Topics</h3>
      {(topicsStage === "pending" || topicsStage === "generating") && (
        <p className="muted">Generating study topics...</p>
      )}
      {topicsStage === "failed" && (
        <p className="error">{topicsError || "Couldn't generate topics."}</p>
      )}
      {topicsStage === "ready" && topics.length === 0 && <p className="muted">No topics found.</p>}
      <ul>
        {topics.map((topic) => (
          <li key={topic.id}>
            <button className="topic-button" onClick={() => onSelectTopic(topic)}>
              {topic.title}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
