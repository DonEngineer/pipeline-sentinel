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


@dataclass
class Incident:
    """One triaged incident: correlated failures plus severity and cause."""

    id: str
    source: str
    severity: str  # low | medium | high | critical
    title: str
    probable_cause: str
    suggested_action: str
    failed_checks: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "severity": self.severity,
            "title": self.title,
            "probable_cause": self.probable_cause,
            "suggested_action": self.suggested_action,
            "failed_checks": self.failed_checks,
            "created_at": self.created_at.isoformat(),
        }
