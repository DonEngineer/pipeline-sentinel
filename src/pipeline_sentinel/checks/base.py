"""Check interface: deterministic, side-effect free, easy to test."""

from __future__ import annotations

from abc import ABC, abstractmethod

from pipeline_sentinel.sources.sql import SqlSource
from pipeline_sentinel.types import CheckResult, Source


class Check(ABC):
    """One verifiable property of a source (volume, freshness, schema, ...)."""

    name: str = "check"

    @abstractmethod
    def run(self, source: Source) -> CheckResult:
        """Run the check; never raise on data problems, report them."""

    def _connector(self, source: Source) -> SqlSource:
        return SqlSource(source)
