# Taco Study Pilot

An AI study companion that turns your PDFs into a chatbot and flashcards.

## Features

- **Upload PDFs** — drop in your course materials to create a workspace.
- **Chat with your documents** — ask questions and get answers grounded in the uploaded PDFs (RAG-powered).
- **Auto-generated topics** — the app extracts key topics from your materials automatically.
- **Flashcards** — generate question/answer flashcards for any topic, on demand.
- **Guest mode** — start studying immediately without creating an account.
- **Live progress updates** — track upload, ingestion, and topic-generation status in real time.

## Tech Stack

- **Backend:** Flask, Celery, SQLAlchemy, Qdrant (vector search)
- **Frontend:** React + Vite

## Getting Started

```bash
# Backend
cd backend
pip install -r requirements.txt
python run.py

# or, from the repo root, bring up everything the backend needs
# (Redis, Qdrant, Ollama, Celery worker, Flask API) in one command:
./scripts/dev.sh

# Frontend
cd frontend
npm install
npm run dev
```

See `backend/.env.example` for required environment variables.
