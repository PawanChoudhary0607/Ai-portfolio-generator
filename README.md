# AI Portfolio Generator — SaaS

Turns a resume PDF into a deployable personal portfolio website, end to
end in the browser. This repo is the SaaS layer built on top of the
finished, frozen `website-generator/` CLI engine.

## Status: SaaS Foundation milestone

This milestone implements the **foundation only**:

| Area | Status |
|---|---|
| Auth (sign up / login / forgot password) | ✅ implemented |
| Dashboard (5 summary panels + Create New Portfolio) | ✅ implemented |
| Upload page (drag & drop → processing progress) | ✅ implemented |
| Backend architecture, API routes, DB schema, navigation | ✅ implemented |
| Theme selection, visual editor, publish, export, deploy, billing, analytics, collaboration | ⏳ later milestones (routes are scaffolded, return `501`) |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the pieces fit
together and why the isolation boundary around `website-generator/`
matters.

## Repository layout

```
website-generator/   The original CLI engine. Untouched. Imported as a
                      library, never modified by the SaaS layer.
backend/              FastAPI app: auth, DB models, API routes, and the
                      one module (services/generator_service.py) allowed
                      to import website-generator/.
frontend/             React + Vite + TypeScript SPA.
shared/               TypeScript types mirroring the backend's Pydantic
                      schemas — the API contract both sides build against.
```

## Running it locally

### 1. Backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # adjust JWT_SECRET_KEY before deploying anywhere real
python3 -m alembic upgrade head   # creates backend/data/app.db
uvicorn app.main:app --reload --port 8000
```

API docs at `http://localhost:8000/docs`.

The upload pipeline's AI analysis step calls a local Ollama server. If
Ollama isn't running, uploads still go through extraction successfully
and then fail (visibly, in the UI) at the "Analyzing resume with AI"
step — that's expected without a local model server, not a bug.

```bash
# To exercise the full pipeline locally:
ollama serve
ollama pull qwen3:14b   # or whatever OLLAMA_MODEL is set to in backend/.env
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env   # points at the backend above by default
npm run dev
```

App at `http://localhost:5173`.

## Why the engine is isolated

`backend/app/services/generator_service.py` is the **only** file in the
backend that imports anything from `website-generator/src`. Every route
and other service calls plain functions on that module, which accept and
return primitives or this backend's own Pydantic types — never the
engine's internal classes past that boundary. That's what makes "do not
modify the generator" enforceable in code, not just in a sentence in a
prompt: nothing else in the codebase has a way to reach in and change it.
