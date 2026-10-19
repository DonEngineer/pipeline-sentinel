"""Schema-drift check: added/removed/changed columns vs a stored snapshot."""

from __future__ import annotations

import json
from pathlib import Path

from pipeline_sentinel.checks.base import Check
from pipeline_sentinel.types import CheckResult, Source


class SchemaDriftCheck(Check):
    """Fail when the table schema differs from the recorded snapshot.

    The first run records the snapshot and passes; later runs compare.
    """

    name = "schema_drift"

    def __init__(self, snapshot_dir: str | Path = ".sentinel") -> None:
        self.snapshot_dir = Path(snapshot_dir)

    def _snapshot_path(self, source: Source) -> Path:
        return self.snapshot_dir / f"schema_{source.name}.json"

    def run(self, source: Source) -> CheckResult:
        current = {c.name: c.type for c in self._connector(source).columns()}
        path = self._snapshot_path(source)
        if not path.exists():
            self.snapshot_dir.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(current, indent=2), encoding="utf-8")
            return CheckResult(
                source=source.name,
                check=self.name,
                passed=True,
                metric=0.0,
                details={"reason": "snapshot recorded", "columns": len(current)},
            )
        expected = json.loads(path.read_text(encoding="utf-8"))
        added = sorted(set(current) - set(expected))
        removed = sorted(set(expected) - set(current))
        changed = sorted(
            name for name in set(current) & set(expected) if current[name] != expected[name]
        )
        drifted = bool(added or removed or changed)
        return CheckResult(
            source=source.name,
            check=self.name,
            passed=not drifted,
            metric=float(len(added) + len(removed) + len(changed)),
            details={"added": added, "removed": removed, "changed": changed},
        )
