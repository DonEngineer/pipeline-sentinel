"""Run the eval: seed a throwaway DB per case, inject, measure detection.

Each case gets a fresh seeded database. The suite runs once to warm stateful
checks (schema snapshots), then the anomaly is injected and the suite runs
again. Everything happens in a temp directory: the real data and the real
``.sentinel`` state are never touched.
"""

from __future__ import annotations

import contextlib
import io
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from pipeline_sentinel.cli import run_suite
from pipeline_sentinel.eval.cases import EVAL_CASES
from pipeline_sentinel.seed import seed


@dataclass
class CaseResult:
    """Outcome of one eval case."""

    name: str
    description: str
    expected: list[str]
    failed: list[str]
    detected: list[str] = field(default_factory=list)
    missed: list[str] = field(default_factory=list)
    false_positives: list[str] = field(default_factory=list)
    ok: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "expected": self.expected,
            "failed": self.failed,
            "detected": self.detected,
            "missed": self.missed,
            "false_positives": self.false_positives,
            "ok": self.ok,
        }


def _case_config(base: Path, db: Path, workdir: Path) -> Path:
    """Point the suite at the case DB; duplicates check uses a natural key.

    Whole-row ``SELECT DISTINCT *`` includes the autoincrement PK, so re-sent
    rows always look distinct. The natural key (loaded_at, amount, customer)
    is what a real pipeline would deduplicate on.
    """
    doc = yaml.safe_load(base.read_text(encoding="utf-8"))
    for source in doc["sources"]:
        source["connection_string"] = f"sqlite:///{db}"
        for check in source.get("checks", []) or []:
            if check["name"] == "duplicates":
                params = dict(check.get("params") or {})
                params.setdefault("columns", ["loaded_at", "amount", "customer"])
                check["params"] = params
    out = workdir / "sentinel.yaml"
    out.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return out


def _quiet_suite(config: str, sentinel_dir: str):
    """Run the suite, swallowing its per-check prints."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return run_suite(config, sentinel_dir=sentinel_dir)


def run_eval(
    config_path: str = "sentinel.yaml",
    days: int = 14,
    only: list[str] | None = None,
) -> list[CaseResult]:
    """Run every eval case; return per-case results."""
    base = Path(config_path)
    cases = [case for case in EVAL_CASES if only is None or case.name in only]
    results: list[CaseResult] = []
    with tempfile.TemporaryDirectory(prefix="sentinel-eval-") as tmp:
        workdir = Path(tmp)
        sentinel_dir = str(workdir / ".sentinel")
        db = workdir / "eval.db"
        config = _case_config(base, db, workdir)
        for case in cases:
            seed(db, days=days)
            _quiet_suite(str(config), sentinel_dir)  # warm stateful checks
            case.inject(str(db))
            suite_results = _quiet_suite(str(config), sentinel_dir)
            failed = sorted(
                f"{result.source}.{result.check}" for result in suite_results if not result.passed
            )
            expected = sorted(case.expected)
            detected = [name for name in failed if name in expected]
            missed = [name for name in expected if name not in failed]
            false_positives = [name for name in failed if name not in expected]
            results.append(
                CaseResult(
                    name=case.name,
                    description=case.description,
                    expected=expected,
                    failed=failed,
                    detected=detected,
                    missed=missed,
                    false_positives=false_positives,
                    ok=not missed and not false_positives,
                )
            )
    return results
