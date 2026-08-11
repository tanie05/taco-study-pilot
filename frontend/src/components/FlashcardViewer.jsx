import { useEffect, useState } from "react";
import { generateFlashcards } from "../services/api";

// Full-page flashcard viewer for the current topic. This is the same
// generate-on-demand + prev/next/flip behavior as the old FlashcardModal,
// just without the modal overlay/close button — FlashcardsPage renders it
// directly in the main content area.
export default function FlashcardViewer({ topic }) {
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
    <div className="flashcard-viewer">
      <h2 className="flashcard-viewer-title">{topic.title}</h2>

      {loading && <p className="muted">Generating flashcards...</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && current && (
        <>
          <div
            className={`flashcard ${flipped ? "flipped" : ""}`}
            onClick={() => setFlipped((f) => !f)}
          >
            <div className="flashcard-inner">
              <div className="flashcard-face flashcard-face-front">{current.question}</div>
              <div className="flashcard-face flashcard-face-back">{current.answer}</div>
            </div>
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
  );
}
