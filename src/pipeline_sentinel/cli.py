"""Command-line interface.

Usage:
    python -m pipeline_sentinel.seed --db data/demo.db
    python -m pipeline_sentinel.cli check --db data/demo.db --source feed_a
"""

from __future__ import annotations

import argparse

from pipeline_sentinel import history
from pipeline_sentinel.checks import (
    FreshnessCheck,
    NullRateCheck,
    RowCountCheck,
    SchemaDriftCheck,
)
from pipeline_sentinel.config import settings
from pipeline_sentinel.types import CheckResult, Source

# Per-source null checks for the demo database (M2 makes this configurable).
NULL_COLUMNS = {"feed_a": "customer"}


def default_checks(source: Source) -> list:
    """Check suite applied to every source in M1."""
    checks = [
        RowCountCheck(
            baseline_days=settings.baseline_days,
            threshold_pct=settings.volume_threshold_pct,
        ),
        FreshnessCheck(max_age_hours=settings.max_age_hours),
        SchemaDriftCheck(snapshot_dir=settings.sentinel_dir),
    ]
    if source.name in NULL_COLUMNS:
        checks.append(
            NullRateCheck(column=NULL_COLUMNS[source.name], max_null_rate=settings.max_null_rate)
        )
    return checks


def run_checks(source: Source) -> list[CheckResult]:
    """Run the default suite; print a summary; log to history."""
    results = [check.run(source) for check in default_checks(source)]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.source}.{result.check} metric={result.metric}")
        if not result.passed:
            print(f"       details={result.details}")
    history.append_results(results, settings.sentinel_dir)
    return results


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(prog="sentinel", description="Pipeline Sentinel CLI.")
    sub = parser.add_subparsers(dest="command", required=True)

    check_cmd = sub.add_parser("check", help="Run checks against one source table.")
    check_cmd.add_argument("--db", default=settings.default_db, help="SQLite database path.")
    check_cmd.add_argument("--source", required=True, help="Table/source name.")

    args = parser.parse_args(argv)
    if args.command == "check":
        source = Source(
            name=args.source,
            connection_string=f"sqlite:///{args.db}",
            table=args.source,
        )
        results = run_checks(source)
        return 0 if all(r.passed for r in results) else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
