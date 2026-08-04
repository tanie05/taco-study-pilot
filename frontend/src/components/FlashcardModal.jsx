import { useEffect, useState } from "react";
import { generateFlashcards } from "../services/api";

export default function FlashcardModal({ topic, onClose }) {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    generateFlashcards(topic.id)
      .then((data) => {
        if (!cancelled) setCards(data.flashcards);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.response?.data?.error || "Failed to generate flashcards.");
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [topic.id]);

  const current = cards[index];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{topic.title}</h2>
          <button onClick={onClose}>Close</button>
        </div>

        {loading && <p>Generating flashcards...</p>}
        {error && <p className="error">{error}</p>}

        {!loading && !error && current && (
          <>
            <div className="flashcard" onClick={() => setFlipped((f) => !f)}>
              {flipped ? current.answer : current.question}
            </div>
            <div className="flashcard-controls">
              <button
                disabled={index === 0}
                onClick={() => {
                  setIndex((i) => i - 1);
                  setFlipped(false);
                }}
              >
                Prev
              </button>
              <span>
                {index + 1} / {cards.length}
              </span>
              <button
                disabled={index === cards.length - 1}
                onClick={() => {
                  setIndex((i) => i + 1);
                  setFlipped(false);
                }}
              >
                Next
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
