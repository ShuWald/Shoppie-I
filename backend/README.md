# FastAPI Backend

This folder contains a lightweight FastAPI service for the hackathon app.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health` - basic health check
- `POST /api/chat` - starter chat endpoint for future LangChain integration
- `GET /docs` - FastAPI interactive API docs

## Frontend CORS

The backend allows requests from the default Next.js dev server at `http://localhost:3000`.