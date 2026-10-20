"""Synthetic anomaly injectors: break a seeded DB on purpose.

Each injector mutates a throwaway SQLite database and returns how many rows
it touched. Row selection happens in Python (no SQLite date-function quirks):
seeded timestamps are UTC ISO strings, so prefix/bounds comparisons are exact.
"""

from __future__ import annotations

import random
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

DbPath = str | Path


def _latest_prefix(db: DbPath, table: str) -> str:
    """Date prefix (``YYYY-MM-DD``) of the newest row: the latest batch."""
    with sqlite3.connect(db) as con:
        row = con.execute(f"SELECT MAX(loaded_at) FROM {table}").fetchone()
    newest = row[0] if row else None
    return newest[:10] if newest else ""


def drop_today(db: DbPath, table: str, fraction: float = 0.5, seed_value: int = 7) -> int:
    """Delete ``fraction`` of the latest batch's rows (simulates a partial load)."""
    rng = random.Random(seed_value)
    with sqlite3.connect(db) as con:
        rowids = [
            row[0]
            for row in con.execute(
                f"SELECT rowid FROM {table} WHERE loaded_at LIKE ?",
                (_latest_prefix(db, table) + "%",),
            )
        ]
        kill = rng.sample(rowids, int(len(rowids) * fraction))
        con.executemany(f"DELETE FROM {table} WHERE rowid = ?", [(r,) for r in kill])
        return len(kill)


def stale_days(db: DbPath, table: str, days: int = 3) -> int:
    """Delete every row newer than ``days`` days ago (simulates a stalled feed)."""
    cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
    with sqlite3.connect(db) as con:
        rowids = [
            row[0]
            for row in con.execute(f"SELECT rowid, loaded_at FROM {table}")
            if row[1] >= cutoff
        ]
        con.executemany(f"DELETE FROM {table} WHERE rowid = ?", [(r,) for r in rowids])
        return len(rowids)


def inject_nulls(
    db: DbPath, table: str, column: str, fraction: float = 0.06, seed_value: int = 7
) -> int:
    """Set ``column`` to NULL on ``fraction`` of rows (simulates a source bug)."""
    rng = random.Random(seed_value)
    with sqlite3.connect(db) as con:
        rowids = [row[0] for row in con.execute(f"SELECT rowid FROM {table}")]
        kill = rng.sample(rowids, int(len(rowids) * fraction))
        con.executemany(f"UPDATE {table} SET {column} = NULL WHERE rowid = ?", [(r,) for r in kill])
        return len(kill)


def duplicate_batch(db: DbPath, table: str, fraction: float = 0.2, seed_value: int = 7) -> int:
    """Re-insert copies of the latest batch's rows minus the PK (re-sent batch)."""
    rng = random.Random(seed_value)
    with sqlite3.connect(db) as con:
        cols = [info[1] for info in con.execute(f"PRAGMA table_info({table})") if info[1] != "id"]
        col_list = ", ".join(cols)
        rows = con.execute(
            f"SELECT {col_list} FROM {table} WHERE loaded_at LIKE ?",
            (_latest_prefix(db, table) + "%",),
        ).fetchall()
        dupes = rng.sample(rows, int(len(rows) * fraction))
        placeholders = ", ".join("?" * len(cols))
        con.executemany(f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})", dupes)
        return len(dupes)


def push_out_of_range(
    db: DbPath,
    table: str,
    column: str,
    value: float = -50.0,
    fraction: float = 0.05,
    seed_value: int = 7,
) -> int:
    """Set ``column`` to an out-of-range ``value`` on ``fraction`` of rows."""
    rng = random.Random(seed_value)
    with sqlite3.connect(db) as con:
        rowids = [row[0] for row in con.execute(f"SELECT rowid FROM {table}")]
        kill = rng.sample(rowids, int(len(rowids) * fraction))
        con.executemany(
            f"UPDATE {table} SET {column} = ? WHERE rowid = ?",
            [(value, r) for r in kill],
        )
        return len(kill)


def add_column(db: DbPath, table: str, column: str = "new_field") -> int:
    """Add a column (simulates an upstream schema change)."""
    with sqlite3.connect(db) as con:
        con.execute(f"ALTER TABLE {table} ADD COLUMN {column} TEXT")
        return 1
