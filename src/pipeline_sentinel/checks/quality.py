"""Data-quality checks: null rates, duplicates, and value ranges."""

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


class DuplicateCheck(Check):
    """Fail when the duplicate-row fraction exceeds ``max_duplicate_rate``.

    Duplicates share the same ``columns`` key; the whole row when ``None``.
    """

    name = "duplicates"

    def __init__(
        self,
        columns: list[str] | None = None,
        max_duplicate_rate: float = 0.01,
    ) -> None:
        self.columns = columns
        self.max_duplicate_rate = max_duplicate_rate

    def run(self, source: Source) -> CheckResult:
        rate = self._connector(source).duplicate_rate(self.columns)
        return CheckResult(
            source=source.name,
            check=self.name,
            passed=rate <= self.max_duplicate_rate,
            metric=round(rate, 4),
            details={
                "columns": self.columns or ["*"],
                "max_duplicate_rate": self.max_duplicate_rate,
            },
        )


class RangeCheck(Check):
    """Fail when the out-of-range fraction of ``column`` is too high."""

    name = "range"

    def __init__(
        self,
        column: str,
        min_value: float,
        max_value: float,
        max_out_of_range_rate: float = 0.01,
    ) -> None:
        self.column = column
        self.min_value = min_value
        self.max_value = max_value
        self.max_out_of_range_rate = max_out_of_range_rate

    def run(self, source: Source) -> CheckResult:
        rate = self._connector(source).out_of_range_rate(
            self.column, self.min_value, self.max_value
        )
        return CheckResult(
            source=source.name,
            check=self.name,
            passed=rate <= self.max_out_of_range_rate,
            metric=round(rate, 4),
            details={
                "column": self.column,
                "min_value": self.min_value,
                "max_value": self.max_value,
                "max_out_of_range_rate": self.max_out_of_range_rate,
            },
        )
