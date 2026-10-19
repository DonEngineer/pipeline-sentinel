"""Generate the demo database: two feeds with 14 days of healthy history.

Usage:
    python -m pipeline_sentinel.seed --db data/demo.db

Tables:
- ``feed_a``: id, loaded_at, amount, customer (~2% NULL customers)
- ``feed_b``: id, loaded_at, status
"""

from __future__ import annotations

import argparse
import random
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, text


def seed(db_path: str | Path, days: int = 14, seed_value: int = 42) -> Path:
    """Create (or replace) the demo database; return its path."""
    rng = random.Random(seed_value)
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    engine = create_engine(f"sqlite:///{path}")
    now = datetime.now(UTC).replace(hour=8, minute=0, second=0, microsecond=0)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE feed_a (id INTEGER PRIMARY KEY, loaded_at TEXT, "
                "amount REAL, customer TEXT)"
            )
        )
        conn.execute(
            text("CREATE TABLE feed_b (id INTEGER PRIMARY KEY, loaded_at TEXT, status TEXT)")
        )
        for day_offset in range(days - 1, -1, -1):
            day = now - timedelta(days=day_offset)
            for _ in range(1000 + rng.randint(-50, 50)):
                customer = None if rng.random() < 0.02 else f"cust_{rng.randint(1, 200)}"
                conn.execute(
                    text(
                        "INSERT INTO feed_a (loaded_at, amount, customer) "
                        "VALUES (:ts, :amount, :customer)"
                    ),
                    {
                        "ts": day.isoformat(),
                        "amount": round(rng.uniform(10, 500), 2),
                        "customer": customer,
                    },
                )
            for _ in range(500 + rng.randint(-30, 30)):
                conn.execute(
                    text("INSERT INTO feed_b (loaded_at, status) VALUES (:ts, :status)"),
                    {
                        "ts": day.isoformat(),
                        "status": rng.choice(["ok", "ok", "ok", "retry"]),
                    },
                )
    return path


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the seeder."""
    parser = argparse.ArgumentParser(prog="sentinel-seed", description="Build the demo database.")
    parser.add_argument("--db", default="data/demo.db", help="SQLite path to create.")
    parser.add_argument("--days", type=int, default=14, help="Days of history.")
    args = parser.parse_args(argv)
    path = seed(args.db, days=args.days)
    print(f"demo database written to {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
