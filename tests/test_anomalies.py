"""Tests for duplicate and range checks (real SQLite, no mocks)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine, text

from pipeline_sentinel.checks import DuplicateCheck, RangeCheck
from pipeline_sentinel.types import Source


def _source(db: Path, table: str = "events") -> Source:
    return Source(name=table, connection_string=f"sqlite:///{db}", table=table)


def _write_db(path: Path, rows: list[tuple[str, float, str | None]]) -> None:
    engine = create_engine(f"sqlite:///{path}")
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE events "
                "(id INTEGER PRIMARY KEY, loaded_at TEXT, amount REAL, customer TEXT)"
            )
        )
        for ts, amount, customer in rows:
            conn.execute(
                text(
                    "INSERT INTO events (loaded_at, amount, customer) "
                    "VALUES (:ts, :amount, :customer)"
                ),
                {"ts": ts, "amount": amount, "customer": customer},
            )


def _row(ts: str, amount: float = 100.0, customer: str | None = "cust_1"):
    return (ts, amount, customer)


def _ts() -> str:
    return datetime.now(UTC).isoformat()


def test_duplicates_passes_without_duplicates(tmp_path):
    db = tmp_path / "t.db"
    _write_db(db, [_row(_ts(), customer=f"cust_{i}") for i in range(50)])
    result = DuplicateCheck(columns=["customer"], max_duplicate_rate=0.01).run(_source(db))
    assert result.passed
    assert result.metric == 0.0


def test_duplicates_fails_above_threshold(tmp_path):
    db = tmp_path / "t.db"
    rows = [_row(_ts(), customer=f"cust_{i}") for i in range(80)]
    rows += [_row(_ts(), customer="dup") for _ in range(20)]
    _write_db(db, rows)
    result = DuplicateCheck(columns=["customer"], max_duplicate_rate=0.01).run(_source(db))
    assert not result.passed
    assert result.metric is not None and result.metric > 0.01
    assert result.details["columns"] == ["customer"]


def test_duplicates_whole_row_when_no_columns(tmp_path):
    db = tmp_path / "t.db"
    engine = create_engine(f"sqlite:///{db}")
    ts = _ts()
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE dupes (loaded_at TEXT, amount REAL, customer TEXT)"))
        for _ in range(2):
            conn.execute(text("INSERT INTO dupes VALUES (:ts, 100.0, 'cust_1')"), {"ts": ts})
        conn.execute(text("INSERT INTO dupes VALUES (:ts, 100.0, 'cust_2')"), {"ts": ts})
    result = DuplicateCheck(max_duplicate_rate=0.01).run(_source(db, "dupes"))
    assert not result.passed
    assert result.details["columns"] == ["*"]


def test_range_passes_within_bounds(tmp_path):
    db = tmp_path / "t.db"
    _write_db(db, [_row(_ts(), amount=float(v)) for v in range(10, 110, 10)])
    result = RangeCheck(column="amount", min_value=0, max_value=1000).run(_source(db))
    assert result.passed


def test_range_fails_on_outliers(tmp_path):
    db = tmp_path / "t.db"
    rows = [_row(_ts(), amount=100.0) for _ in range(90)]
    rows += [_row(_ts(), amount=99999.0) for _ in range(10)]
    _write_db(db, rows)
    result = RangeCheck(
        column="amount", min_value=0, max_value=1000, max_out_of_range_rate=0.01
    ).run(_source(db))
    assert not result.passed
    assert result.metric == 0.1
