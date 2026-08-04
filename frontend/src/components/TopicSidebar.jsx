export default function TopicSidebar({ topics, onSelectTopic }) {
  return (
    <div className="topic-sidebar">
      <h3>Flashcard Topics</h3>
      {topics.length === 0 && <p className="muted">No topics found.</p>}
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
