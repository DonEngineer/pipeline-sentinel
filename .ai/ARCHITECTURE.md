# Pipeline Sentinel — architecture

## Data flow

```
Source (SQL table)
  → SqlSource (SQLAlchemy; SQLite demo, SQL Server prod)
  → Checks: RowCountCheck · FreshnessCheck · SchemaDriftCheck · NullRateCheck
  → CheckResult {source, check, passed, metric, details, checked_at}
  → history.jsonl (append-only)
  → [M2] rule engine → [M3] triage agent → [M4] scheduler + dashboard
```

## Key decisions

- **Checks are pure functions of (source, config).** No network except the DB
  read, no LLM, no side effects besides returning a `CheckResult`. This makes
  them trivially unit-testable against real SQLite files.
- **Dialect-agnostic SQL.** Timestamp bucketing happens in Python, not in
  `DATE_TRUNC`/`CAST` — the same check code runs on SQLite and SQL Server.
- **Timestamps are UTC-aware end to end.** Naive ISO strings from the DB are
  parsed as UTC; `datetime.now(UTC)` is the only "now".
- **Schema snapshots are files, not tables.** `.sentinel/schema_<source>.json`
  keeps M1 dependency-free and diffable; a DB-backed store can replace it.
- **Rules gate, the agent analyzes.** A failed check is always recorded. The
  triage agent (M3) may correlate and prioritize, but never silently drops a
  failure — this is a deliberate anti-footgun rule.

## Failure modes considered

- Empty table → freshness fails with `reason: table is empty` (not a crash).
- No baseline history → volume check passes with `reason: no baseline history
  yet` (avoids false alarms on new sources).
- First schema run → records the snapshot and passes (bootstrap, not drift).
- Unparseable judge/agent output (M3/M5) → scores degrade to safe defaults,
  raw output preserved in details.
