"""Tests for the JSONL check-result history log."""

from __future__ import annotations

from pipeline_sentinel import history
from pipeline_sentinel.types import CheckResult


def test_history_append_and_read_roundtrip(tmp_path):
    results = [
        CheckResult(source="feed_a", check="row_count", passed=True, metric=0.05),
        CheckResult(source="feed_a", check="freshness", passed=False, metric=48.0),
    ]
    history.append_results(results, tmp_path)
    history.append_results(results[:1], tmp_path)
    entries = history.read_history(tmp_path)
    assert len(entries) == 3
    assert entries[0]["check"] == "row_count"
    assert entries[1]["passed"] is False
    assert entries[2]["checked_at"]


def test_read_history_empty_when_no_log(tmp_path):
    assert history.read_history(tmp_path) == []
