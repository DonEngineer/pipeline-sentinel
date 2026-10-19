"""Append-only JSONL logs of check results and incidents (feeds the M4 dashboard)."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline_sentinel.types import CheckResult, Incident


def append_results(results: list[CheckResult], sentinel_dir: str | Path = ".sentinel") -> Path:
    """Append results to the history log; return the log path."""
    path = Path(sentinel_dir) / "history.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for result in results:
            fh.write(json.dumps(result.to_dict()) + "\n")
    return path


def read_history(sentinel_dir: str | Path = ".sentinel", limit: int = 200) -> list[dict]:
    """Read the most recent ``limit`` history entries (oldest first)."""
    path = Path(sentinel_dir) / "history.jsonl"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-limit:] if line.strip()]


def append_incidents(incidents: list[Incident], sentinel_dir: str | Path = ".sentinel") -> Path:
    """Append incidents to the incident log; return the log path."""
    path = Path(sentinel_dir) / "incidents.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for incident in incidents:
            fh.write(json.dumps(incident.to_dict()) + "\n")
    return path


def read_incidents(sentinel_dir: str | Path = ".sentinel", limit: int = 200) -> list[dict]:
    """Read the most recent ``limit`` incidents (oldest first)."""
    path = Path(sentinel_dir) / "incidents.jsonl"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-limit:] if line.strip()]
