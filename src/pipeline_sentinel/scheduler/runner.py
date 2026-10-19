"""APScheduler wiring: run the suite + triage on an interval."""

from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler

from pipeline_sentinel.types import Incident


def run_once(
    config_path: str,
    only_source: str | None = None,
    triage_failures: bool = True,
) -> list[Incident]:
    """Run the suite once and triage failures (unless disabled)."""
    from pipeline_sentinel.cli import run_triage

    return run_triage(config_path, only_source, triage_failures=triage_failures)


def start(
    config_path: str,
    interval_minutes: int = 60,
    only_source: str | None = None,
    triage_failures: bool = True,
) -> None:
    """Run immediately, then every ``interval_minutes`` until interrupted."""
    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_once,
        "interval",
        minutes=interval_minutes,
        args=[config_path, only_source, triage_failures],
        id="sentinel",
        max_instances=1,
    )
    print(f"Watching {config_path} every {interval_minutes} minutes. Ctrl+C to stop.")
    run_once(config_path, only_source, triage_failures)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Stopped.")
