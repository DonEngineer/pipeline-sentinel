# Pipeline Sentinel

[![CI](https://github.com/DonEngineer/pipeline-sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/DonEngineer/pipeline-sentinel/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

An **agentic data pipeline watchdog**: scheduled checks watch your data sources for volume drops, stale batches, schema drift, and quality regressions — then an LLM triage agent correlates the failures into one incident with severity and a probable root cause, instead of spamming raw alerts.

Silent pipeline failures are usually discovered by the customer. This project is the watchdog you wish you had: deterministic checks where exactness matters, agentic judgment where noise needs reducing. Everything runs local for $0.

## How it works

```
            ┌──────────────┐
            │   Sources    │──► SQL Server / SQLite tables
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │    Checks    │──► volume · freshness · schema · quality
            └──────┬───────┘
                   ▼
            ┌──────────────┐    all pass
            │ Rule engine  │──────────────► log + dashboard (green)
            └──────┬───────┘
                   │ failures
                   ▼
            ┌──────────────┐
            │ Triage agent │──► correlate → severity → root cause → alert
            └──────────────┘         (LangGraph + local LLM)
```

Design principle: **deterministic where it must be exact** (checks, thresholds), **agentic where judgment helps** (triage, correlation, alert text). The LLM never silently suppresses a failure — rules are the gate, the agent is the analyst.

## Features

- 🔍 Deterministic checks: row-count vs baseline, freshness, schema drift, null rates
- 🗄️ SQLAlchemy sources: SQL Server in production, SQLite for the local demo
- 🤖 LangGraph triage agent: correlates failed checks into incidents (M3)
- ⏰ Scheduled runs via APScheduler (M4)
- 📊 Streamlit dashboard: source health, check history, alerts (M4)
- 🧪 Eval harness with synthetic anomaly injection (M5)

## Quickstart

**Prerequisites:** Python 3.11+.

```bash
# 1. Install
pip install -e ".[dev]"

# 2. Build the demo database (two feeds, 14 days of healthy history)
python -m pipeline_sentinel.seed --db data/demo.db

# 3. Run checks against a source  (M1)
python -m pipeline_sentinel.cli check --db data/demo.db --source feed_a
```

To watch it catch a real anomaly, delete half of today's rows from `feed_b` and re-run the check — the volume check fails with the deviation in the details.

Copy `.env.example` to `.env` to override thresholds, the state directory, or the Ollama model.

## Project structure

```
src/pipeline_sentinel/
├── checks/        Deterministic checks: volume, freshness, schema, quality  (M1)
├── sources/       SQLAlchemy source connector (SQL Server / SQLite)        (M1)
├── history.py     Append-only JSONL log of check results                    (M1)
├── seed.py        Demo database generator                                    (M1)
├── cli.py         check / seed commands                                      (M1)
├── triage/        LangGraph triage agent                                     (M3)
└── scheduler/     APScheduler wiring                                         (M4)
app/               Streamlit dashboard                                        (M4)
evals/             Anomaly-injection eval harness                             (M5)
data/              Demo databases (gitignored)
.sentinel/         Schema snapshots + check history (gitignored)
.ai/               Handoff docs for AI-assisted development
```

## Roadmap

| Milestone | Status |
|---|---|
| M1 Check engine: sources, checks, history, seed, CLI | ✅ Done |
| M2 Anomaly rules: duplicates, ranges, configurable suites | ⬜ Next |
| M3 LangGraph triage agent: correlate → severity → root cause | ⬜ |
| M4 Scheduler + Streamlit dashboard | ⬜ |
| M5 Eval harness (synthetic anomaly injection) + polish | ⬜ |

Stretch goals: Great Expectations integration, webhook/PagerDuty alerts, dbt source support.

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Checks | SQLAlchemy + hand-rolled rules | Deterministic, testable, no heavy deps |
| Triage | LangGraph + Ollama | Agentic correlation, free and local |
| Scheduling | APScheduler | In-process, zero infra |
| Dashboard | Streamlit | Fastest credible demo |
| Evals | Custom harness | Transparent detection/false-positive metrics |

## License

MIT — see [LICENSE](LICENSE).
