"""Tests for YAML suite loading and check construction."""

from __future__ import annotations

import pytest

from pipeline_sentinel.checks import NullRateCheck, RowCountCheck
from pipeline_sentinel.suite import CheckSpec, build_check, load_suite, to_source

SUITE_YAML = """
sources:
  - name: feed_a
    connection_string: sqlite:///data/demo.db
    table: feed_a
    timestamp_column: loaded_at
    checks:
      - name: row_count
        params: {baseline_days: 7, threshold_pct: 0.3}
      - name: null_rate
        params: {column: customer, max_null_rate: 0.05}
  - name: feed_b
    connection_string: sqlite:///data/demo.db
"""


def test_load_suite_parses_sources_and_checks(tmp_path):
    path = tmp_path / "sentinel.yaml"
    path.write_text(SUITE_YAML, encoding="utf-8")
    specs = load_suite(path)
    assert len(specs) == 2
    assert specs[0].name == "feed_a"
    assert specs[0].table == "feed_a"
    assert specs[0].timestamp_column == "loaded_at"
    assert [c.name for c in specs[0].checks] == ["row_count", "null_rate"]
    assert specs[0].checks[0].params == {"baseline_days": 7, "threshold_pct": 0.3}


def test_load_suite_applies_defaults(tmp_path):
    path = tmp_path / "sentinel.yaml"
    path.write_text(SUITE_YAML, encoding="utf-8")
    specs = load_suite(path)
    assert specs[1].table == "feed_b"  # defaults to source name
    assert specs[1].timestamp_column == "loaded_at"
    assert specs[1].checks == []


def test_build_check_constructs_with_params():
    check = build_check(CheckSpec(name="row_count", params={"baseline_days": 5}))
    assert isinstance(check, RowCountCheck)
    assert check.baseline_days == 5


def test_build_check_null_rate():
    check = build_check(CheckSpec(name="null_rate", params={"column": "c"}))
    assert isinstance(check, NullRateCheck)


def test_build_check_unknown_name_raises():
    with pytest.raises(ValueError, match="unknown check"):
        build_check(CheckSpec(name="nope"))


def test_to_source_converts_spec(tmp_path):
    path = tmp_path / "sentinel.yaml"
    path.write_text(SUITE_YAML, encoding="utf-8")
    source = to_source(load_suite(path)[0])
    assert source.name == "feed_a"
    assert source.table == "feed_a"
    assert source.connection_string == "sqlite:///data/demo.db"
