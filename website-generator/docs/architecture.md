# Architecture Overview

## Separation of Concerns

| Layer | Location | Rule |
|---|---|---|
| UI | `app/` | No business logic. Calls `src/` only. |
| Business Logic | `src/` | No Streamlit imports. No UI code. |
| Prompt Templates | `prompts/` | Plain `.txt` files. No Python. |
| Data | `data/` | Never committed. Gitignored. |
| Config | `.env` | Never committed. Gitignored. |

## LLM Provider Abstraction

All LLM providers implement a shared interface defined in `src/llm/base.py`.
Application code calls the interface — never a concrete provider directly.
Switching from Ollama to OpenAI requires a config change, not a code change.

## Data Flow

```
PDF Upload → Parser → Resume JSON (Pydantic) → LLM → Portfolio JSON (Pydantic) → UI
```

## Decision Records

See `docs/decisions/` for Architecture Decision Records (ADRs).
