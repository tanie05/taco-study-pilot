import { useState } from "react";

export default function UploadDropzone({ onFilesSelected }) {
  const [dragOver, setDragOver] = useState(false);

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const files = Array.from(e.dataTransfer.files).filter((f) =>
      f.name.toLowerCase().endsWith(".pdf")
    );
    if (files.length) onFilesSelected(files);
  }

  function handleChange(e) {
    const files = Array.from(e.target.files);
    if (files.length) onFilesSelected(files);
  }

  return (
    <div
      className={`dropzone ${dragOver ? "dropzone-active" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
    >
      <p>Drag & drop PDF files here, or</p>
      <label className="file-picker">
        Choose files
        <input type="file" accept=".pdf" multiple hidden onChange={handleChange} />
      </label>
    </div>
  );
}
