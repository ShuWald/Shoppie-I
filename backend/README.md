FastAPI backend


## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Note: main.py is the entry point, so reserved for routing logic only

## Endpoints
- `GET /docs` - Docs for all our configured routes
- `GET /test` - Testing route (Maybe delete after testing?)

## Frontend CORS
The backend allows requests from the default Next.js dev server at `http://localhost:3000`