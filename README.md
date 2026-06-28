<div align="center">

[![Portfolio AI](assets/banner.png)](assets/banner.png)

# Portfolio AI

**Turn a resume PDF into a deployable portfolio website — analyzed by a local AI model, not a third-party API.**

**[Live Demo](https://ai-portfolio-generator-smoky.vercel.app/) · [API Docs](https://ai-portfolio-generator-production-8f9f.up.railway.app/docs)**

[![FastAPI](https://img.shields.io/badge/backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/frontend-React%2019-149ECA?style=flat-square&logo=react&logoColor=white)](https://react.dev/)
[![Ollama](https://img.shields.io/badge/AI-Ollama%20%2F%20Qwen3-6E56CF?style=flat-square)](https://ollama.com/)
[![Tests](https://img.shields.io/badge/tests-779%20passing-2ea44f?style=flat-square)](#-tech-stack)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](#-license)

</div>

<br/>

[![Portfolio AI demo](assets/demo.gif)](assets/demo.gif)

<br/>

## Why this exists

Most "AI resume tools" send your resume to someone else's API. This one runs the model — Qwen3, via Ollama — on infrastructure you control.

Upload a PDF, pick from five real themes, and get a working static website. No deploy step required to see the result.

<br/>

## Features

| | |
|---|---|
| **🔒 Auth & Security**<br/>JWT auth, signature-validated uploads, every route scoped to its owner. | **🤖 Local AI**<br/>Resume analysis runs on Qwen3 via Ollama — nothing leaves your machine. |
| **🎨 Five Real Themes**<br/>Minimal, Executive, Developer, Creative, Modern SaaS — different layouts, not palette swaps. | **⚡ Instant Switching**<br/>Changing themes re-renders the page only — extraction and AI analysis never re-run. |
| **🌐 Live Preview**<br/>The generated site renders in-browser before you export anything. | **📦 HTML / ZIP Export**<br/>One click for a self-contained HTML file or a zipped static site. |

<br/>

## Screenshots

[![Dashboard](assets/dashboard.png)](assets/dashboard.png)

| | |
|---|---|
| [![Upload](assets/upload.png)](assets/upload.png) | [![Processing](assets/processing.png)](assets/processing.png) |
| [![Theme Gallery](assets/themes.png)](assets/themes.png) | [![Generated Website](assets/website-preview.png)](assets/website-preview.png) |
| [![Results](assets/results.png)](assets/results.png) | [![Support](assets/support.png)](assets/support.png) |

<br/>

## How it works

```
Resume PDF → Extract → AI Analysis → Portfolio JSON → Theme Renderer → Static Website → Export
```

Every stage has its own test suite — 779 passing tests, independent of the SaaS layer around it.

<br/>

## Architecture

[![Architecture](assets/architecture.png)](assets/architecture.png)

`website-generator/` is a frozen engine that handles extraction, AI analysis, and rendering. The SaaS layer talks to it through exactly one file, `generator_service.py` — so the engine can evolve without the rest of the app noticing.

<br/>

## Project structure

```
ai-portfolio-saas/
├── backend/             FastAPI — auth, resumes, portfolios, dashboard
├── frontend/            React + Vite SPA
├── website-generator/   Frozen AI/rendering engine — 779 passing tests
├── shared/               Cross-stack API types
└── docs/                 Architecture & API reference
```

<br/>

## Getting started

```bash
git clone <this-repo-url> && cd ai-portfolio-saas

cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
alembic upgrade head && uvicorn app.main:app --reload

cd ../frontend
npm install && cp .env.example .env && npm run dev
```

Backend → `localhost:8000/docs` · Frontend → `localhost:5173`

For real AI analysis: `ollama serve && ollama pull qwen3:14b`

<br/>

## Deployment

| Vercel | Railway | Docker |
|---|---|---|
| Root: `frontend/`, auto-deploys on push | Builds from root `Dockerfile`, health check at `/health` | `docker build -t portfolio-ai .` |

<br/>

## Built like production software

- One isolation boundary — only `generator_service.py` may import the engine
- 779 passing tests, decoupled from the SaaS layer
- Schema-validated AI output, never trusted as raw text
- Unfinished features show as honest empty states, not silent failures

<br/>

## Roadmap

- [ ] One-click publish to a live URL
- [ ] Draft autosave
- [ ] Version history
- [ ] Visual theme editor

<br/>

## License

MIT

<br/>

<div align="center">

**Pawan Choudhary**

</div>
