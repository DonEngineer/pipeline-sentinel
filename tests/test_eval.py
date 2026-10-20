"""Tests for the eval harness (throwaway DBs; no LLM involved)."""

from __future__ import annotations

from pathlib import Path

from pipeline_sentinel.eval import EVAL_CASES, injectors, run_eval
from pipeline_sentinel.seed import seed

CONFIG = Path(__file__).resolve().parent.parent / "sentinel.yaml"


def test_eval_cases_are_defined():
    names = [case.name for case in EVAL_CASES]
    assert "baseline" in names
    assert len(names) == len(set(names))


def test_injectors_touch_rows(tmp_path):
    db = tmp_path / "demo.db"
    seed(db, days=10)
    assert injectors.drop_today(db, "feed_a", fraction=0.5) > 400
    assert injectors.inject_nulls(db, "feed_a", "customer", fraction=0.06) > 400
    assert injectors.duplicate_batch(db, "feed_a", fraction=0.2) > 80
    assert injectors.push_out_of_range(db, "feed_a", "amount", -50.0, 0.05) > 400
    assert injectors.stale_days(db, "feed_a", days=3) > 2000
    assert injectors.add_column(db, "feed_a") == 1


def test_eval_detects_anomalies_without_false_positives():
    results = run_eval(str(CONFIG), days=10, only=["baseline", "volume_drop", "null_spike"])
    by_name = {result.name: result for result in results}
    assert by_name["baseline"].ok, by_name["baseline"].to_dict()
    assert by_name["volume_drop"].ok, by_name["volume_drop"].to_dict()
    assert by_name["null_spike"].ok, by_name["null_spike"].to_dict()
