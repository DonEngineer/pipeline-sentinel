"""Eval case definitions: anomaly -> checks expected to fail."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from pipeline_sentinel.eval import injectors


@dataclass
class EvalCase:
    """One anomaly scenario. ``expected`` lists ``source.check`` names that must fail."""

    name: str
    description: str
    inject: Callable[[str], None]
    expected: list[str] = field(default_factory=list)


def _on_feed_a(fn: Callable, **kwargs) -> Callable[[str], None]:
    def inject(db: str) -> None:
        fn(db, "feed_a", **kwargs)

    return inject


EVAL_CASES: list[EvalCase] = [
    EvalCase(
        name="baseline",
        description="Healthy data: nothing should fail.",
        inject=lambda db: None,
        expected=[],
    ),
    EvalCase(
        name="volume_drop",
        description="Half of today's feed_a rows deleted.",
        inject=_on_feed_a(injectors.drop_today, fraction=0.5),
        expected=["feed_a.row_count"],
    ),
    EvalCase(
        name="stale_feed",
        description="feed_a stalled 3 days ago (latest batch is complete, just old).",
        inject=_on_feed_a(injectors.stale_days, days=3),
        expected=["feed_a.freshness"],
    ),
    EvalCase(
        name="null_spike",
        description="6% of feed_a customers nulled.",
        inject=_on_feed_a(injectors.inject_nulls, column="customer", fraction=0.06),
        expected=["feed_a.null_rate"],
    ),
    EvalCase(
        name="duplicate_batch",
        description="20% of today's feed_a rows re-sent.",
        inject=_on_feed_a(injectors.duplicate_batch, fraction=0.2),
        expected=["feed_a.duplicates"],
    ),
    EvalCase(
        name="out_of_range",
        description="5% of feed_a amounts set to -50.",
        inject=_on_feed_a(injectors.push_out_of_range, column="amount", value=-50.0, fraction=0.05),
        expected=["feed_a.range"],
    ),
    EvalCase(
        name="schema_change",
        description="New column added to feed_a.",
        inject=_on_feed_a(injectors.add_column, column="new_field"),
        expected=["feed_a.schema_drift"],
    ),
]
