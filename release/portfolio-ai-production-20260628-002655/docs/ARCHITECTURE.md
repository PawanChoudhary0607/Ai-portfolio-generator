# Architecture — SaaS Foundation milestone

## Goals this milestone actually serves

The product brief describes a 6-step flow (upload → process → theme
select → edit → publish → export) and a long list of future features
(billing, analytics, collaboration, deploy). Building all of it at once
is how a codebase ends up with five half-finished features and zero
finished ones. This milestone deliberately implements a narrow vertical
slice — **auth through "resume processed"** — completely and correctly,
with the database schema and route structure already shaped for what
comes next, instead of guessing at editor/publish requirements before
they're specified.

## Request flow (what's implemented)

```
Browser (React SPA)
   │  fetch / XHR, JWT in Authorization header
   ▼
FastAPI app (backend/app/main.py)
   │
   ├─ api/routes/auth.py ────────► services/auth_service.py ──► database/models.py (User, PasswordResetToken)
   ├─ api/routes/dashboard.py ───► database/models.py (read-only aggregation)
   ├─ api/routes/resumes.py ─────► services/resume_service.py ─┐
   └─ api/routes/portfolios.py    (list/get + 501 stubs)       │
                                                                 ▼
                                              services/generator_service.py
                                                 (the ONLY import of website-generator/src)
                                                                 ▼
                                              website-generator/  (frozen engine, untouched)
```

## The isolation boundary, concretely

`generator_service.py` exposes plain functions —
`extract_resume_text`, `parse_resume`, `analyze_resume`,
`generate_portfolio`, `render_theme_preview`,
`render_theme_to_directory` — that take/return dicts and backend
Pydantic models. It adds `website-generator/` to `sys.path` and imports
the engine's internal modules (`src.extraction`, `src.ai`,
`src.portfolio`, `src.website`) — but it is the *only* file that does.
Every engine exception type gets caught here and re-raised as a single
`GeneratorServiceError(stage, message)`, so the rest of the backend
only ever handles one error shape regardless of which pipeline stage
failed.

Consequence: the engine could be replaced, versioned independently, or
moved behind its own microservice later by rewriting this one file.

## Pipeline orchestration

`services/resume_service.py` runs four steps per upload — extraction,
AI analysis, portfolio generation, and a website-generation sanity
render — updating `Resume`/`Portfolio` row status after each one so the
frontend's polling `GET /resumes/{id}/status` always reflects real,
current state rather than a guess. It currently runs via FastAPI
`BackgroundTasks` (in-process, after the response is sent). That's
adequate for local dev and for one user at a time; the code includes an
explicit note that production needs a real task queue (Celery/RQ/Arq)
since each Ollama call takes seconds and ties up a request worker
otherwise. This is the most likely thing to revisit when "thousands of
users" stops being aspirational.

## Database schema

All eight required entities exist now (`backend/app/database/models.py`):
`User`, `PasswordResetToken`, `Resume`, `Portfolio`, `ThemeSelection`,
`Draft`, `PublishedSite`, `DeploymentStatus`, `VersionHistory`. Only
`User`, `PasswordResetToken`, `Resume`, and `Portfolio` are written to by
routes implemented so far — the rest exist so the Theme
Selection/Editor/Publish milestones build on a stable schema instead of
needing a migration that touches rows already in production.

Migrations are managed with Alembic (`backend/alembic/`), wired to read
the database URL and model metadata from the app itself
(`alembic/env.py`) so the schema source of truth is always the
SQLAlchemy models, never a hand-maintained SQL file.

## API surface

Implemented now: signup, login, me, forgot/reset password, dashboard
overview, resume upload, resume list/get/status, portfolio list/get,
theme catalog.

Routed but stubbed (`501 Not Implemented`) so the contract is stable for
frontend work ahead of the backend: theme preview generation, draft
save, portfolio update, publish, delete, ZIP export. A stub is
deliberately distinct from a missing route — a 404 here would mean "this
isn't part of the plan," a 501 means "this is coming."

## Frontend

React + Vite + TypeScript, React Router for navigation, Tailwind for
styling against the white/orange/no-purple/no-gradient design system
specified in the brief. `AuthContext` holds the logged-in user and JWT
(stored in `localStorage`); `ProtectedRoute` gates the dashboard/upload
routes; `AppShell` is the persistent sidebar nav, with not-yet-built
destinations (Theme selection, Visual editor, Publish & export) shown
disabled and labeled "soon" rather than omitted — so the navigation
structure communicates the full intended product, not just what exists
today.

`shared/types.ts` mirrors the backend's Pydantic schemas by hand. There's
no codegen step yet (e.g. from the OpenAPI schema) — for a single-team,
single-repo project at this stage that's a reasonable tradeoff, but it's
worth automating once the API surface grows past what's comfortable to
keep in sync manually.

## Deliberately not built yet

Theme preview rendering for all 5 themes, the visual editor, publish,
ZIP/JSON/HTML export, one-click deploy, billing, analytics, and
collaboration. Each has at least a route stub and/or a database table
already in place; none has business logic, because none has been
scoped and reviewed as its own milestone yet.
