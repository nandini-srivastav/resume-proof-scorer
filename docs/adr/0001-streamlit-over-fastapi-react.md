# ADR 0001: Use Streamlit instead of FastAPI + React

## Status

Accepted

## Context

The project needs a UI for uploading resumes, reviewing extracted job
skills, and viewing ranked results with per-candidate evidence. Two
realistic options: a FastAPI backend with a React frontend, or a
single-file Streamlit app.

This is a portfolio project built solo on a fixed 14-day timeline, where
the goal is to demonstrate system design, backend logic, and AI
integration — not frontend engineering. Every day spent on API
boilerplate, CORS config, and frontend state management is a day not
spent on the parsing, scoring, and verification logic that's the actual
point of the project.

## Decision

Use Streamlit for the entire UI layer, backed by a single `process_resume()`
orchestration function that calls the same plain Python modules
(`parser`, `baseline_scorer`, `llm_scorer`, `github_verifier`,
`aggregator`) a FastAPI backend would have called anyway.

## Consequences

- Faster to build: no separate API layer, no frontend build tooling, no
  CORS or auth setup between two services.
- Session state (`st.session_state`) replaces what would otherwise be
  client-side React state — sufficient for a 3-view app (setup, results,
  detail), but wouldn't scale cleanly to a more complex UI.
- Deployment is simpler (Streamlit Community Cloud, one process) than
  running and coordinating two separate services.
- Trade-off: less control over UI polish and interaction patterns than
  React would offer (e.g. no per-row buttons inside a real data table —
  worked around with a manual `st.columns()` row loop instead).
- The core logic modules remain framework-agnostic — if this ever needed
  a React frontend later, only `app.py` would need to be replaced; the
  scoring pipeline itself has no Streamlit dependency.
