export default function ConfirmDialog({ title, message, confirmLabel = "Confirm", confirming, onConfirm, onCancel }) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{title}</h2>
        </div>
        <p>{message}</p>
        <div className="flashcard-controls">
          <button onClick={onCancel} disabled={confirming}>
            Cancel
          </button>
          <button className="btn-danger" onClick={onConfirm} disabled={confirming}>
            {confirming ? "Working..." : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
