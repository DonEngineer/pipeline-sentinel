"""YAML-declared check suites: which checks run on each source.

Example (``sentinel.yaml``)::

    sources:
      - name: feed_a
        connection_string: sqlite:///data/demo.db
        table: feed_a
        checks:
          - name: row_count
            params: {baseline_days: 7, threshold_pct: 0.3}
          - name: null_rate
            params: {column: customer, max_null_rate: 0.05}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from pipeline_sentinel import checks as check_pkg
from pipeline_sentinel.checks.base import Check
from pipeline_sentinel.config import settings
from pipeline_sentinel.types import Source

CHECK_REGISTRY: dict[str, type[Check]] = {
    "row_count": check_pkg.RowCountCheck,
    "freshness": check_pkg.FreshnessCheck,
    "schema_drift": check_pkg.SchemaDriftCheck,
    "null_rate": check_pkg.NullRateCheck,
    "duplicates": check_pkg.DuplicateCheck,
    "range": check_pkg.RangeCheck,
}


@dataclass
class CheckSpec:
    name: str
    params: dict = field(default_factory=dict)


@dataclass
class SourceSpec:
    name: str
    connection_string: str
    table: str
    timestamp_column: str = "loaded_at"
    checks: list[CheckSpec] = field(default_factory=list)


def load_suite(path: str | Path) -> list[SourceSpec]:
    """Parse a suite YAML file into source specs."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    specs = []
    for entry in data.get("sources", []):
        specs.append(
            SourceSpec(
                name=entry["name"],
                connection_string=entry["connection_string"],
                table=entry.get("table", entry["name"]),
                timestamp_column=entry.get("timestamp_column", "loaded_at"),
                checks=[
                    CheckSpec(name=item["name"], params=dict(item.get("params") or {}))
                    for item in entry.get("checks", [])
                ],
            )
        )
    return specs


def build_check(spec: CheckSpec) -> Check:
    """Instantiate a check from its spec; raises ValueError on unknown names."""
    try:
        cls = CHECK_REGISTRY[spec.name]
    except KeyError:
        raise ValueError(f"unknown check: {spec.name!r}") from None
    params = dict(spec.params)
    if spec.name == "schema_drift":
        params.setdefault("snapshot_dir", settings.sentinel_dir)
    return cls(**params)


def to_source(spec: SourceSpec) -> Source:
    """Convert a source spec into a runtime Source."""
    return Source(
        name=spec.name,
        connection_string=spec.connection_string,
        table=spec.table,
        timestamp_column=spec.timestamp_column,
    )
