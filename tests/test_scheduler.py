"""Tests for the scheduler (no real waiting; triage disabled)."""

from __future__ import annotations

from dataclasses import replace

from pipeline_sentinel import config as config_mod
from pipeline_sentinel import history
from pipeline_sentinel.scheduler import run_once
from pipeline_sentinel.seed import seed

SUITE_YAML = """
sources:
  - name: feed_a
    connection_string: sqlite:///{db}
    table: feed_a
    checks:
      - name: row_count
        params: {baseline_days: 7, threshold_pct: 0.3}
      - name: freshness
        params: {max_age_hours: 48}
"""


def _use_tmp_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "pipeline_sentinel.cli.settings",
        replace(config_mod.settings, sentinel_dir=str(tmp_path)),
    )


def test_run_once_runs_suite_and_logs_history(tmp_path, monkeypatch):
    db = tmp_path / "demo.db"
    seed(db, days=10)
    config = tmp_path / "sentinel.yaml"
    config.write_text(SUITE_YAML.replace("{db}", str(db)), encoding="utf-8")
    _use_tmp_settings(tmp_path, monkeypatch)
    incidents = run_once(str(config), triage_failures=False)
    assert incidents == []
    entries = history.read_history(str(tmp_path))
    assert len(entries) == 2
    assert all(entry["passed"] for entry in entries)


def test_run_once_reports_failures_without_triage(tmp_path, monkeypatch):
    from pipeline_sentinel.eval import injectors

    db = tmp_path / "demo.db"
    seed(db, days=10)
    injectors.stale_days(db, "feed_a", days=3)  # deterministic failure, any time of day
    config = tmp_path / "sentinel.yaml"
    config.write_text(SUITE_YAML.replace("{db}", str(db)), encoding="utf-8")
    _use_tmp_settings(tmp_path, monkeypatch)
    incidents = run_once(str(config), triage_failures=False)
    assert incidents == []  # triage disabled, so no incidents even on failure
    entries = history.read_history(str(tmp_path))
    assert any(not entry["passed"] for entry in entries)
