# Pipeline Sentinel — AI handoff context

> Read this file first when continuing work on this project in a new session
> or with a different model (Claude, Gemini, ChatGPT).

## What this is

Portfolio project #2: an agentic data pipeline watchdog. Scheduled checks watch
tabular sources (volume, freshness, schema drift, quality); a rule engine flags
deviations; a LangGraph triage agent correlates failures into incidents with
severity and probable root cause. Goal: a public, recruiter-readable repo
demonstrating AI Engineer skills — data engineering, agentic orchestration,
and evals — grounded in the owner's day job (multi-million-row data channels).

## Stack (approved 2026-10-19)

- Checks: **SQLAlchemy** + hand-rolled rules (deterministic, dialect-agnostic —
  timestamp bucketing happens in Python)
- Triage: **LangGraph** + **Ollama** local (`llama3.1`); never silently suppresses
- Sources: SQLAlchemy (SQL Server `mssql+pyodbc://` in prod, SQLite for demo)
- Scheduling: APScheduler · Dashboard: Streamlit · Evals: custom harness
- Python 3.11+, `pip install -e ".[dev]"`, ruff + pytest in CI

## Hard rules

1. **100% of repo content in ENGLISH** — code, comments, docstrings, README,
   commit messages, `.ai/` files. Never let Spanish slip in.
2. Keep dependencies light; justify every new one in the commit message.
3. No paid APIs in the default path. Flag any paid-API need before using it.
4. Checks are deterministic and never raise on data problems — they report them.
   The triage agent analyzes; rules decide.

## Milestones

M1 check engine ✅ → M2 anomaly rules ✅ → M3 triage agent ✅ → M4 scheduler+dashboard ✅
→ M5 evals+polish. See README roadmap for details.

## Conventions

- `src/pipeline_sentinel/<area>/` — one concern per package.
- Config via env vars with sane local defaults (`config.py`); `.env.example`
  documents them. Check suites are YAML (`sentinel.yaml`); `suite.py` maps
  check names to classes via `CHECK_REGISTRY`.
- Timestamps are timezone-aware UTC everywhere (`datetime.now(UTC)`); the DB
  layer parses naive ISO strings as UTC.
- State (schema snapshots, history JSONL) lives in `.sentinel/` (gitignored).
- Commits: imperative mood, English, e.g. `Add null-rate quality check`.
- Tests live in `tests/`; CI runs ruff + pytest on every push.
