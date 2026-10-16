# SmartRoll

SmartRoll is a web-based attendance app. Faculty sign in with Google, create a class session, and display a rotating QR code. Students scan the code, sign in with Google, and check in from their phones.

## Project layout

- `frontend/` — React and Vite single-page app
- `backend/` — FastAPI API using SQLAlchemy and PostgreSQL
- [UI/UX specification](UI_UX_SPEC.md)
- [Deployment guide](DEPLOYMENT.md) — Cloudflare Pages, Render, and Supabase free tiers

## Run locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000
```

Set `GOOGLE_CLIENT_ID`, `FACULTY_EMAILS`, and a local PostgreSQL `DATABASE_URL` in `backend/.env`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Set `VITE_GOOGLE_CLIENT_ID` to the same Google OAuth Web client ID and `VITE_API_URL=http://localhost:8000` in `frontend/.env`.

The `.env` files are ignored by Git. Do not commit credentials or database connection strings.
