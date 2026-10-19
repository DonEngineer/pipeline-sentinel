"""Row-count check: today's volume vs the trailing baseline."""

from __future__ import annotations

from datetime import date

from pipeline_sentinel.checks.base import Check
from pipeline_sentinel.types import CheckResult, Source


class RowCountCheck(Check):
    """Fail when today's row count deviates from baseline by ``threshold_pct``.

    Baseline is the mean daily count over ``baseline_days`` (excluding today).
    """

    name = "row_count"

    def __init__(self, baseline_days: int = 7, threshold_pct: float = 0.3) -> None:
        self.baseline_days = baseline_days
        self.threshold_pct = threshold_pct

    def run(self, source: Source) -> CheckResult:
        counts = self._connector(source).row_counts_by_date(self.baseline_days + 1)
        today = date.today()
        today_count = counts.get(today, 0)
        baseline_counts = [c for d, c in counts.items() if d != today]
        if not baseline_counts:
            return CheckResult(
                source=source.name,
                check=self.name,
                passed=True,
                metric=float(today_count),
                details={"reason": "no baseline history yet"},
            )
        baseline = sum(baseline_counts) / len(baseline_counts)
        deviation = abs(today_count - baseline) / baseline if baseline else 0.0
        return CheckResult(
            source=source.name,
            check=self.name,
            passed=deviation <= self.threshold_pct,
            metric=deviation,
            details={
                "today": today_count,
                "baseline": round(baseline, 1),
                "threshold_pct": self.threshold_pct,
            },
        )
