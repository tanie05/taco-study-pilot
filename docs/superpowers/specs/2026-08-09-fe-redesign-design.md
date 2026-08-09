# Frontend Redesign — Chat Page + Flashcards Page

*Date: 2026-08-09*

## Goal

Redesign the frontend around two pages, adopting a pastel pink/lavender + purple accent visual style (inspired by the provided example image), and add a persistent left sidebar in the style of ChatGPT for workspace/nav.

1. **Main page** — merges the current upload flow and chat flow into one screen with a persistent left sidebar.
2. **Flashcards page** — a dedicated full page (not a modal) for browsing topics and studying flashcards.

This is purely a frontend visual/structural redesign. No backend changes.

## Scope

- One workspace per user remains a hard backend limit — unchanged. The sidebar is built to visually accommodate multiple workspaces/recent chats in the future, but today it will only ever show the current single workspace.
- No routing library is introduced. Page switching (`chat` vs `flashcards`) is local React state in `App.jsx`, consistent with the app's existing no-router pattern.
- Existing functionality (upload, add files, delete workspace, SSE ingestion progress, chat, topic/flashcard generation and caching) is preserved as-is on the backend. This redesign only changes component structure and styling on the frontend.

## Page 1: Main Page (Chat)

Replaces the current `checking → upload → loading → ready/failed` full-screen swap with a single persistent shell: **left sidebar + main content area**, where the main content area changes based on app state.

### Left sidebar (new, persistent across both pages)

- Logo/brand ("🌮 taco") at top.
- Nav items: **Chat** and **Flashcards** — clicking switches the main content (Flashcards is disabled/greyed out until a workspace is `ready`).
- **Workspace card**: shows the current workspace name (derived from uploaded files, e.g. first filename or a generic label), file count, and status (`processing…` / `ready`). Not shown in empty state (no workspace yet).
- **Recent** section: lists the current workspace as a single entry when one exists. Styled as a list so it visually reads as "recent chats," ready for future multi-workspace support without functional multi-workspace logic today.
- Sidebar is always visible; it does not change between empty/loading/chat states except for what the workspace card shows.

### Main content area — state-driven

Reuses the app's existing states, rendered inside the persistent shell instead of as separate full-page swaps:

1. **`checking`** — brief loading spinner (session restore via `GET /workspace/mine`), sidebar shows no workspace yet.
2. **`upload` (empty state)** — replaces `UploadPage`. Centered greeting ("Hi, I am taco, your AI study assistant"), bold headline, and a card-style input box with an **Attach** pill (opens file picker, same drag/drop support as today's `UploadDropzone` — dropzone behavior is preserved, just restyled into this input-box shape) and a send button. Submitting triggers the existing `POST /upload` flow.
3. **`loading`** — replaces `LoadingPage`. Same shell, main area shows the SSE-driven ingestion stage messages, still centered, styled consistently with the empty state (softer, no chat header yet).
4. **`ready` (chat)** — replaces the chat portion of `WorkspacePage`. Chat header (workspace name), scrollable message thread (user bubbles right/purple, bot bubbles left/white), input bar pinned to bottom (same attach-pill + send-button styling as the empty state, for visual consistency). No flashcard/topic UI here anymore — moved entirely to Page 2.
5. **`failed`** — error state, same shell, message + retry action in the main area.

`AddFilesModal` and `ConfirmDialog` remain as overlays triggered from the workspace card (e.g. an overflow/kebab menu on the card for "Add files" / "Delete workspace"), restyled to match the pastel/purple aesthetic but functionally unchanged.

## Page 2: Flashcards Page

A dedicated page, navigated to only via the sidebar "Flashcards" nav item (no entry point from the chat header). Only reachable/enabled when the workspace is `ready`.

- Same persistent left sidebar as Page 1 (Chat is now the inactive nav item).
- **Left panel (within main content)**: topic list for the current workspace — replaces `TopicSidebar`'s current role, restyled. Shows topic titles; clicking one selects it and loads its flashcards. Reflects the existing `topics` SSE track (pending/generating/ready/failed) for the generating state.
- **Main area**: flashcards for the selected topic — replaces `FlashcardModal`'s content, moved out of a modal into this full-page layout. Keeps the existing flip-card + prev/next interaction and the existing on-demand generation + DB-caching behavior (`POST /topics/<id>/generate`). Empty state ("select a topic to see flashcards") when no topic is selected yet.

## Visual style (applies to both pages)

- Background: soft pink → lavender gradient (`#fbeef6` → `#f6e4f2`).
- Sidebar background: light lavender (`#f3e6f5`), 1px border `#e6d9ec`.
- Accent/primary: purple `#7c3aed` (buttons, active nav state, user chat bubbles).
- Cards/inputs: white, rounded corners (12–16px), soft purple-tinted shadow.
- Typography: existing sans-serif stack, bold headline weight for greeting text.
- No new UI/component library — continues with plain CSS (no Tailwind), extending `App.css`/`index.css` and adding a stylesheet per new/restructured component as the current codebase already does per-component.

## Component changes

| Current | New |
|---|---|
| `App.jsx` (full-page state swap) | `App.jsx` renders persistent `Sidebar` + routes main content by state and by `currentPage` (`chat` \| `flashcards`) |
| `pages/UploadPage.jsx` | Folded into a `ChatPage` empty-state render path |
| `pages/LoadingPage.jsx` | Folded into `ChatPage` loading-state render path |
| `pages/WorkspacePage.jsx` (chat + topics + flashcards combined) | Split: `ChatPage` (chat only) and `FlashcardsPage` (topics + flashcards) |
| `components/TopicSidebar.jsx` | Restyled, moved into `FlashcardsPage` as the left topic-panel |
| `components/FlashcardModal.jsx` | Restyled into a non-modal `FlashcardsPage` main-area view |
| `components/ChatWindow.jsx`, `UploadDropzone.jsx`, `AddFilesModal.jsx`, `ConfirmDialog.jsx` | Kept, restyled |
| *(new)* `components/Sidebar.jsx` | New persistent left nav + workspace card + recent list |

No changes to `services/api.js` — all existing endpoints/SSE subscriptions are reused as-is.

## Out of scope

- Multi-workspace backend support.
- Real authentication/signup.
- New routing library.
- Any backend API changes.
