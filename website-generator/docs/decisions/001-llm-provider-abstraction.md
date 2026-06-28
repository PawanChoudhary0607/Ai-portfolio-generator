# ADR 001 — LLM Provider Abstraction

**Date:** 2024-06  
**Status:** Accepted

## Context

The initial implementation uses Ollama + Qwen2 running locally.
Future milestones will support OpenAI, Gemini, and Anthropic Claude.
Hardcoding Ollama would require a refactor to add each new provider.

## Decision

Define an abstract base class (`src/llm/base.py`) that all LLM providers implement.
Application code depends only on the abstract interface, never on a concrete provider.
The active provider is selected via the `LLM_PROVIDER` environment variable.

## Consequences

- Adding a new provider requires implementing one class, not modifying callers.
- Testing is simpler — the interface can be mocked without a running LLM.
- Slight upfront complexity in exchange for long-term flexibility.
