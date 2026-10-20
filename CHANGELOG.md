# Changelog

## 0.1.0 — 2026-10-19

First release of Pipeline Sentinel, an agentic data pipeline watchdog.

- **M1 — Check engine.** SQL source connector (SQLAlchemy; SQL Server in
  production, SQLite for the demo), four deterministic checks
  (RowCount, Freshness, SchemaDrift, NullRate), append-only JSONL history,
  demo seeder, and CLI. 13 tests.
- **M2 — Anomaly rules.** DuplicateCheck (natural key or whole row) and
  RangeCheck, YAML check suites with a check registry (unknown names fail
  fast), CLI rewritten around `--config`. 24 tests.
- **M3 — Triage agent.** LangGraph agent (`correlate → hypothesize`) groups
  failures by source into incidents: deterministic severity rules
  (stale/collapsed volume → critical), LLM-written probable cause and
  suggested action, logged to `incidents.jsonl`. New `triage` CLI command.
  29 tests.
- **M4 — Scheduler + dashboard.** APScheduler watch loop (`watch` command,
  `--triage/--no-triage`) and a Streamlit dashboard: source health,
  incidents with severity and root cause, check history, and a
  "Run checks now" button. 31 tests.
- **M5 — Eval harness + polish.** Synthetic anomaly injection
  (`volume_drop`, `stale_feed`, `null_spike`, `duplicate_batch`,
  `out_of_range`, `schema_change`, plus a healthy `baseline`): 6/6 expected
  failures detected, 0 false positives. `eval` CLI command, this changelog,
  and a demo walkthrough in the README. 34 tests.
