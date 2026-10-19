"""Core domain types shared by checks, triage, and the dashboard."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass(frozen=True)
class Source:
    """A tabular data source to watch."""

    name: str
    connection_string: str
    table: str
    timestamp_column: str = "loaded_at"


@dataclass(frozen=True)
class ColumnInfo:
    name: str
    type: str


@dataclass
class CheckResult:
    """Outcome of a single check run against a source."""

    source: str
    check: str
    passed: bool
    metric: float | None
    details: dict = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "check": self.check,
            "passed": self.passed,
            "metric": self.metric,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
        }
