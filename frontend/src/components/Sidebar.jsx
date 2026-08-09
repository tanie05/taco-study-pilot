import { useEffect, useRef, useState } from "react";

// Persistent left nav shown on both the Chat and Flashcards pages. Only
// ever shows one workspace today (one-workspace-per-user is a hard backend
// limit — see backend/app/api/upload.py), but is laid out so a future
// multi-workspace "Recent" list only needs more entries, not a redesign.
export default function Sidebar({
  currentPage,
  onNavigate,
  workspace,
  flashcardsEnabled,
  onAddFiles,
  onDeleteWorkspace,
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const workspaceCardRef = useRef(null);

  useEffect(() => {
    if (!menuOpen) return;

    function handleClickOutside(event) {
      if (
        workspaceCardRef.current &&
        !workspaceCardRef.current.contains(event.target)
      ) {
        setMenuOpen(false);
      }
    }

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [menuOpen]);

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">🌮 taco</div>

      <nav className="sidebar-nav">
        <button
          className={`sidebar-nav-item ${currentPage === "chat" ? "active" : ""}`}
          onClick={() => onNavigate("chat")}
        >
          💬 Chat
        </button>
        <button
          className={`sidebar-nav-item ${currentPage === "flashcards" ? "active" : ""}`}
          onClick={() => onNavigate("flashcards")}
          disabled={!flashcardsEnabled}
        >
          🎴 Flashcards
        </button>
      </nav>

      {workspace && (
        <>
          <div className="sidebar-section-label">Workspace</div>
          <div className="sidebar-workspace-card" ref={workspaceCardRef}>
            <div className="sidebar-workspace-name">My Workspace</div>
            <div className="sidebar-workspace-meta">
              {workspace.fileCount} file{workspace.fileCount === 1 ? "" : "s"} ·{" "}
              {workspace.status}
            </div>
            <button
              className="sidebar-workspace-menu-btn"
              onClick={() => setMenuOpen((open) => !open)}
              aria-label="Workspace options"
            >
              ⋯
            </button>
            {menuOpen && (
              <div className="sidebar-workspace-menu">
                <button
                  onClick={() => {
                    setMenuOpen(false);
                    onAddFiles();
                  }}
                >
                  Add files
                </button>
                <button
                  className="btn-danger"
                  onClick={() => {
                    setMenuOpen(false);
                    onDeleteWorkspace();
                  }}
                >
                  Delete workspace
                </button>
              </div>
            )}
          </div>

          <div className="sidebar-section-label">Recent</div>
          <div className="sidebar-recent-item active">My Workspace</div>
        </>
      )}
    </aside>
  );
}
