# AI Portfolio Generator

> Transform your resume into a professional portfolio website using local AI — no cloud API keys required.

A production-grade AI engineering project demonstrating clean architecture, LLM provider abstraction, and full-stack Python development with Streamlit and Ollama.

---

## Project Status

| Milestone | Description | Status |
|---|---|---|
| 1 | Project Foundation | ✅ Complete |
| 2 | PDF Parsing + JSON Schema | 🔜 Next |
| 3 | LLM Integration (Ollama + Qwen2) | ⬜ Pending |
| 4 | Streamlit UI | ⬜ Pending |
| 5 | Website Export | ⬜ Pending |

---

## Architecture

```
User uploads PDF
       ↓
  Resume Parser       (src/parsers/)
       ↓
  Structured JSON     (src/schemas/)
       ↓
  LLM Provider        (src/llm/)
       ↓
  Portfolio Content   (src/schemas/)
       ↓
  Streamlit UI        (app/)
```

**Design principles:**
- `src/` contains all business logic — zero UI code
- `app/` contains all Streamlit code — zero business logic
- `prompts/` contains all LLM prompt templates — no prompts hardcoded in Python
- `data/` is fully gitignored — no user data ever enters version control
- LLM providers are interchangeable via a shared interface

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| AI — local | Ollama + Qwen2:7b |
| AI — future | OpenAI, Gemini, Claude |
| Data validation | Pydantic v2 |
| PDF parsing | PyMuPDF |
| Config | python-dotenv |
| Linting | Ruff |
| Formatting | Black |
| Type checking | Mypy |
| Testing | Pytest |

---

## Prerequisites

- Python 3.11.x
- [Ollama](https://ollama.com) installed and running locally
- Qwen2 model pulled:

```bash
ollama pull qwen2:7b
```

---

## Quickstart

```bash
# 1. Clone the repository
git clone https://github.com/your-username/ai-portfolio-generator.git
cd ai-portfolio-generator

# 2. Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — no changes needed for local Ollama default settings

# 5. Run the application
streamlit run main.py
```

---

## Project Structure

```
ai-portfolio-generator/
│
├── app/                    # Streamlit UI components (no business logic)
├── src/
│   ├── parsers/            # PDF → structured JSON
│   ├── llm/                # LLM provider abstraction + implementations
│   ├── schemas/            # Pydantic models: Resume, Portfolio
│   └── utils/              # Shared utilities (logging, file I/O)
├── prompts/                # LLM prompt templates as plain .txt files
├── tests/                  # Unit and integration tests
├── docs/                   # Architecture notes and decision records
├── data/
│   ├── raw/                # Uploaded resumes — gitignored
│   ├── processed/          # Parsed JSON output — gitignored
│   └── samples/            # Sanitized sample data for development
├── scripts/                # Operational utilities (env validation etc.)
├── .env.example            # Environment variable template
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── pyproject.toml          # Tool config: black, ruff, mypy, pytest
└── main.py                 # Application entry point
```

---

## Development

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src

# Format code
black .

# Lint
ruff check .

# Type check
mypy src/
```

---

## Environment Variables

Copy `.env.example` to `.env`. For local development with Ollama, the defaults work without modification.

See `.env.example` for all available configuration options including future cloud LLM provider keys.

---

## Contributing

1. Branch from `main`: `git checkout -b feature/your-feature`
2. Make changes, write tests
3. Run `black .` and `ruff check .` before committing
4. Open a pull request against `main`

---

## License

MIT
