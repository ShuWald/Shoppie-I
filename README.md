Shopping + Social Media App


\- `Projects` directory contains the hackathon track prompts in pdf format
\- `shopie-i/` for the Next.js frontend
    \- `src` directory will contain our code
\- `shopie-i/backend/` for the FastAPI backend
    \- `app` directory will contain our code

**Quick start:**

1. Start the frontend with `npm run dev` inside `shopie-i/`
2. Start the backend with `uvicorn app.main:app --reload --port 8000` inside `backend/`

The frontend can call the backend at http://localhost:8000

**Setup/First time:**

Frontend - 
    \- Node is required, check `node --version`
    \- npm is required, `npm install` after installing node
    \- Navigate to `shopie-i`
    \- Chart.js required, run `npm install chart.js`
    \- `npm run dev` to run frontend
        \- Navigate to link in terminal to see site, local to access on your machine, network to access from another's
        - Local:         http://localhost:3000
        - Network:       http://10.8.197.232:3000

Backend -
    \- Python required
    \- Navigage to backend folder
    \- Create virtual environment `python -m venv venv`
    \- Bypass Error `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`
    \- Activate your virtual environment `venv/Scripts/activate`
    \- Install packages from `requirements.txt` using `pip install -r requirements.txt`
    \- `uvicorn app.main:app --reload --port 8000` to run backend
        \- backend runs on http://127.0.0.1:8000 
