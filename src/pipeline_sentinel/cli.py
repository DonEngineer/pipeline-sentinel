"""Command-line interface.

Usage:
    python -m pipeline_sentinel.seed --db data/demo.db
    python -m pipeline_sentinel.cli check --config sentinel.yaml [--source feed_a]
"""

from __future__ import annotations

import argparse

from pipeline_sentinel import history
from pipeline_sentinel.config import settings
from pipeline_sentinel.suite import build_check, load_suite, to_source
from pipeline_sentinel.types import CheckResult


def run_suite(config_path: str, only_source: str | None = None) -> list[CheckResult]:
    """Run every check of every (selected) source; print; log to history."""
    results: list[CheckResult] = []
    for spec in load_suite(config_path):
        if only_source and spec.name != only_source:
            continue
        source = to_source(spec)
        for check_spec in spec.checks:
            result = build_check(check_spec).run(source)
            results.append(result)
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

    check_cmd = sub.add_parser("check", help="Run a check suite from a YAML config.")
    check_cmd.add_argument("--config", default="sentinel.yaml", help="Suite YAML path.")
    check_cmd.add_argument("--source", default=None, help="Only run this source.")

    args = parser.parse_args(argv)
    if args.command == "check":
        results = run_suite(args.config, args.source)
        return 0 if all(r.passed for r in results) else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
