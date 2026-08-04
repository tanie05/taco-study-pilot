import { useState } from "react";
import UploadDropzone from "../components/UploadDropzone";
import { uploadFiles } from "../services/api";

export default function UploadPage({ onUploaded }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  async function handleUpload() {
    setUploading(true);
    setError(null);
    try {
      const { workspace_id } = await uploadFiles(selectedFiles);
      onUploaded(workspace_id);
    } catch (err) {
      setError(err.response?.data?.error || "Upload failed. Please try again.");
      setUploading(false);
    }
  }

  return (
    <div className="page upload-page">
      <h1>Study Assistant</h1>
      <p>Upload your PDFs and start learning immediately.</p>

      <UploadDropzone onFilesSelected={setSelectedFiles} />

      {selectedFiles.length > 0 && (
        <ul className="file-list">
          {selectedFiles.map((f) => (
            <li key={f.name}>{f.name}</li>
          ))}
        </ul>
      )}

      {error && <p className="error">{error}</p>}

      <button
        disabled={selectedFiles.length === 0 || uploading}
        onClick={handleUpload}
      >
        {uploading ? "Uploading..." : "Upload & Start"}
      </button>
    </div>
  );
}
