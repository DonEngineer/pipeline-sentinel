"""Command-line interface.

Usage:
    python -m pipeline_sentinel.seed --db data/demo.db
    python -m pipeline_sentinel.cli check --config sentinel.yaml [--source feed_a]
    python -m pipeline_sentinel.cli triage --config sentinel.yaml [--source feed_a]
    python -m pipeline_sentinel.cli watch --config sentinel.yaml --interval 60
"""

from __future__ import annotations

import argparse

from pipeline_sentinel import history
from pipeline_sentinel.config import settings
from pipeline_sentinel.suite import build_check, load_suite, to_source
from pipeline_sentinel.triage import build_agent, triage
from pipeline_sentinel.triage.llm import OllamaChat
from pipeline_sentinel.types import CheckResult, Incident


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


def run_triage(
    config_path: str,
    only_source: str | None = None,
    triage_failures: bool = True,
) -> list[Incident]:
    """Run the suite, then triage every failure into incidents (unless disabled)."""
    results = run_suite(config_path, only_source)
    failures = [result for result in results if not result.passed]
    if not failures:
        print("All checks passed — nothing to triage.")
        return []
    if not triage_failures:
        print(f"{len(failures)} check(s) failed — triage skipped (--no-triage).")
        return []
    llm = OllamaChat(model=settings.llm_model, base_url=settings.ollama_base_url)
    incidents = triage(failures, build_agent(llm))
    for incident in incidents:
        print(f"[{incident.severity.upper()}] {incident.id} — {incident.title}")
        print(f"  Probable cause:   {incident.probable_cause}")
        print(f"  Suggested action: {incident.suggested_action}")
    history.append_incidents(incidents, settings.sentinel_dir)
    return incidents


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(prog="sentinel", description="Pipeline Sentinel CLI.")
    sub = parser.add_subparsers(dest="command", required=True)

    check_cmd = sub.add_parser("check", help="Run a check suite from a YAML config.")
    check_cmd.add_argument("--config", default="sentinel.yaml", help="Suite YAML path.")
    check_cmd.add_argument("--source", default=None, help="Only run this source.")

    triage_cmd = sub.add_parser("triage", help="Triage failed checks into incidents.")
    triage_cmd.add_argument("--config", default="sentinel.yaml", help="Suite YAML path.")
    triage_cmd.add_argument("--source", default=None, help="Only triage this source.")

    watch_cmd = sub.add_parser("watch", help="Run the suite on a schedule.")
    watch_cmd.add_argument("--config", default="sentinel.yaml", help="Suite YAML path.")
    watch_cmd.add_argument("--source", default=None, help="Only watch this source.")
    watch_cmd.add_argument("--interval", type=int, default=60, help="Minutes between runs.")
    watch_cmd.add_argument(
        "--triage",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Triage failures with the LLM (needs Ollama running).",
    )

    args = parser.parse_args(argv)
    if args.command == "check":
        results = run_suite(args.config, args.source)
        return 0 if all(r.passed for r in results) else 1
    if args.command == "triage":
        run_triage(args.config, args.source)
        return 0
    if args.command == "watch":
        from pipeline_sentinel.scheduler import start

        start(args.config, args.interval, args.source, args.triage)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
