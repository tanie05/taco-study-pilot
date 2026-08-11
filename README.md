<img width="48" height="42" alt="taco" src="https://github.com/user-attachments/assets/a8824990-ce80-4ea4-9214-8af8ec18e08a" />

# Taco Study Pilot

An AI study companion that turns your PDFs into a chatbot and flashcards.

## Features

- **Upload PDFs** — drop in your course materials to create a workspace.
- **Chat with your documents** — ask questions and get answers grounded in the uploaded PDFs (RAG-powered).
- **Auto-generated topics** — the app extracts key topics from your materials automatically.
- **Flashcards** — generate question/answer flashcards for any topic, on demand.
- **Guest mode** — start studying immediately without creating an account.
- **Live progress updates** — track upload, ingestion, and topic-generation status in real time.


<img width="1509" height="826" alt="Screenshot 2026-08-11 at 1 29 20 PM" src="https://github.com/user-attachments/assets/a09bffde-fb27-466e-bc73-95c6ef674938" />
<img width="1495" height="826" alt="Screenshot 2026-08-11 at 1 34 15 PM" src="https://github.com/user-attachments/assets/ebf712ef-50cf-4a11-b6fe-9c66c6e43adc" />
<img width="1492" height="813" alt="Screenshot 2026-08-11 at 1 44 22 PM" src="https://github.com/user-attachments/assets/44aeb00b-05fd-4c11-9cec-6c02cd1efdfd" />
<img width="1486" height="819" alt="Screenshot 2026-08-11 at 1 49 26 PM" src="https://github.com/user-attachments/assets/e43b8107-97eb-44bc-824a-99b06027a421" />
<img width="1494" height="820" alt="Screenshot 2026-08-11 at 1 33 58 PM" src="https://github.com/user-attachments/assets/1e0aecfd-4925-4290-bcaf-71d154a81d02" />
<img width="1501" height="824" alt="Screenshot 2026-08-11 at 1 36 17 PM" src="https://github.com/user-attachments/assets/e4467b6c-cc14-4b2c-bff5-706d73d48f36" />



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
