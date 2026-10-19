"""Smoke test for the demo database seeder."""

from __future__ import annotations

from sqlalchemy import create_engine, text

from pipeline_sentinel.seed import seed


def test_seed_creates_demo_tables_with_history(tmp_path):
    path = seed(tmp_path / "demo.db", days=14)
    engine = create_engine(f"sqlite:///{path}")
    with engine.connect() as conn:
        count_a = conn.execute(text("SELECT COUNT(*) FROM feed_a")).scalar()
        count_b = conn.execute(text("SELECT COUNT(*) FROM feed_b")).scalar()
        days_a = conn.execute(text("SELECT COUNT(DISTINCT loaded_at) FROM feed_a")).scalar()
    assert count_a > 10_000
    assert count_b > 5_000
    assert days_a == 14
