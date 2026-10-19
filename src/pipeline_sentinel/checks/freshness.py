"""Freshness check: how stale is the newest batch?"""

from __future__ import annotations

from datetime import UTC, datetime

from pipeline_sentinel.checks.base import Check
from pipeline_sentinel.types import CheckResult, Source


class FreshnessCheck(Check):
    """Fail when the newest timestamp is older than ``max_age_hours``."""

    name = "freshness"

    def __init__(self, max_age_hours: float = 26.0) -> None:
        self.max_age_hours = max_age_hours

    def run(self, source: Source) -> CheckResult:
        newest = self._connector(source).max_timestamp()
        if newest is None:
            return CheckResult(
                source=source.name,
                check=self.name,
                passed=False,
                metric=None,
                details={"reason": "table is empty"},
            )
        age_hours = (datetime.now(UTC) - newest).total_seconds() / 3600
        return CheckResult(
            source=source.name,
            check=self.name,
            passed=age_hours <= self.max_age_hours,
            metric=round(age_hours, 2),
            details={"newest": newest.isoformat(), "max_age_hours": self.max_age_hours},
        )
