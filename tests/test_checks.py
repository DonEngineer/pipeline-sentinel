"""Tests for the check engine (real SQLite databases, no mocks)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, text

from pipeline_sentinel.checks import (
    FreshnessCheck,
    NullRateCheck,
    RowCountCheck,
    SchemaDriftCheck,
)
from pipeline_sentinel.types import Source


def _source(db: Path, table: str = "events") -> Source:
    return Source(name=table, connection_string=f"sqlite:///{db}", table=table)


def _write_db(path: Path, table: str, rows: list[tuple[str, str | None]]) -> None:
    engine = create_engine(f"sqlite:///{path}")
    with engine.begin() as conn:
        conn.execute(
            text(f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, loaded_at TEXT, customer TEXT)")
        )
        for ts, customer in rows:
            conn.execute(
                text(f"INSERT INTO {table} (loaded_at, customer) VALUES (:ts, :c)"),
                {"ts": ts, "c": customer},
            )


def _rows(
    days: int, per_day: int, null_frac: float = 0.0, include_today: bool = True
) -> list[tuple[str, str | None]]:
    rows = []
    now = datetime.now(UTC)
    stop = -1 if include_today else 0
    for day_ago in range(days, stop, -1):
        ts = (now - timedelta(days=day_ago)).isoformat()
        for i in range(per_day):
            customer = None if (i / per_day) < null_frac else f"cust_{i}"
            rows.append((ts, customer))
    return rows


def test_row_count_passes_on_stable_volume(tmp_path):
    db = tmp_path / "t.db"
    _write_db(db, "events", _rows(8, 100))
    result = RowCountCheck(baseline_days=7, threshold_pct=0.3).run(_source(db))
    assert result.passed
    assert result.metric is not None and result.metric < 0.3


def test_row_count_fails_on_volume_drop(tmp_path):
    db = tmp_path / "t.db"
    rows = _rows(7, 100, include_today=False) + _rows(0, 40)
    _write_db(db, "events", rows)
    result = RowCountCheck(baseline_days=7, threshold_pct=0.3).run(_source(db))
    assert not result.passed
    assert result.details["today"] == 40
    assert result.metric is not None and result.metric > 0.3


def test_row_count_passes_without_baseline_history(tmp_path):
    db = tmp_path / "t.db"
    _write_db(db, "events", _rows(0, 10))
    result = RowCountCheck(baseline_days=7, threshold_pct=0.3).run(_source(db))
    assert result.passed
    assert result.details["reason"] == "no baseline history yet"


def test_freshness_passes_on_fresh_data(tmp_path):
    db = tmp_path / "t.db"
    ts = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    _write_db(db, "events", [(ts, "cust_1")])
    result = FreshnessCheck(max_age_hours=26).run(_source(db))
    assert result.passed


def test_freshness_fails_on_stale_data(tmp_path):
    db = tmp_path / "t.db"
    ts = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
    _write_db(db, "events", [(ts, "cust_1")])
    result = FreshnessCheck(max_age_hours=26).run(_source(db))
    assert not result.passed
    assert result.metric is not None and result.metric > 26


def test_freshness_fails_on_empty_table(tmp_path):
    db = tmp_path / "t.db"
    _write_db(db, "events", [])
    result = FreshnessCheck(max_age_hours=26).run(_source(db))
    assert not result.passed
    assert result.details["reason"] == "table is empty"


def test_schema_drift_records_snapshot_then_passes(tmp_path):
    db = tmp_path / "t.db"
    _write_db(db, "events", _rows(0, 5))
    check = SchemaDriftCheck(snapshot_dir=tmp_path / ".sentinel")
    first = check.run(_source(db))
    assert first.passed
    assert first.details["reason"] == "snapshot recorded"
    second = check.run(_source(db))
    assert second.passed


def test_schema_drift_detects_added_column(tmp_path):
    db = tmp_path / "t.db"
    _write_db(db, "events", _rows(0, 5))
    check = SchemaDriftCheck(snapshot_dir=tmp_path / ".sentinel")
    assert check.run(_source(db)).passed
    engine = create_engine(f"sqlite:///{db}")
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE events ADD COLUMN new_col TEXT"))
    result = check.run(_source(db))
    assert not result.passed
    assert result.details["added"] == ["new_col"]


def test_null_rate_passes_below_threshold(tmp_path):
    db = tmp_path / "t.db"
    _write_db(db, "events", _rows(1, 100, null_frac=0.02))
    result = NullRateCheck(column="customer", max_null_rate=0.05).run(_source(db))
    assert result.passed


def test_null_rate_fails_above_threshold(tmp_path):
    db = tmp_path / "t.db"
    _write_db(db, "events", _rows(1, 100, null_frac=0.2))
    result = NullRateCheck(column="customer", max_null_rate=0.05).run(_source(db))
    assert not result.passed
    assert result.metric is not None and result.metric > 0.05
