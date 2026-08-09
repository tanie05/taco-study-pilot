import { useState } from "react";
import UploadDropzone from "./UploadDropzone";

export default function AddFilesModal({ onSubmit, onClose }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit() {
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit(selectedFiles);
    } catch (err) {
      setError(err.response?.data?.error || "Failed to add files. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Add more files</h2>
          <button onClick={onClose} disabled={submitting}>
            Close
          </button>
        </div>

        <p className="muted">
          New files join this workspace, and topics/flashcards are regenerated from everything
          uploaded so far.
        </p>

        <UploadDropzone onFilesSelected={setSelectedFiles} />

        {selectedFiles.length > 0 && (
          <ul className="file-list">
            {selectedFiles.map((f) => (
              <li key={f.name}>{f.name}</li>
            ))}
          </ul>
        )}

        {error && <p className="error">{error}</p>}

        <div className="flashcard-controls">
          <button onClick={onClose} disabled={submitting}>
            Cancel
          </button>
          <button disabled={selectedFiles.length === 0 || submitting} onClick={handleSubmit}>
            {submitting ? "Uploading..." : "Add files"}
          </button>
        </div>
      </div>
    </div>
  );
}
