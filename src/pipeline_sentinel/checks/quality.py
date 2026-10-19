"""Data-quality checks: null rates today (duplicates and ranges arrive in M2)."""

from __future__ import annotations

from pipeline_sentinel.checks.base import Check
from pipeline_sentinel.types import CheckResult, Source


class NullRateCheck(Check):
    """Fail when the NULL fraction of ``column`` exceeds ``max_null_rate``."""

    name = "null_rate"

    def __init__(self, column: str, max_null_rate: float = 0.05) -> None:
        self.column = column
        self.max_null_rate = max_null_rate

    def run(self, source: Source) -> CheckResult:
        rate = self._connector(source).null_rate(self.column)
        return CheckResult(
            source=source.name,
            check=self.name,
            passed=rate <= self.max_null_rate,
            metric=round(rate, 4),
            details={"column": self.column, "max_null_rate": self.max_null_rate},
        )
