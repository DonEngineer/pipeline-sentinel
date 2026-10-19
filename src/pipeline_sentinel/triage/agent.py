"""LangGraph triage agent: failed checks -> incident with severity and cause.

Graph (per source): ``correlate -> hypothesize``.

Severity is scored by deterministic rules — the rules gate, the LLM analyzes.
The agent never drops a failure; every failed check lands in an incident.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TypedDict

from langgraph.graph import END, StateGraph

from pipeline_sentinel.triage.prompts import HYPOTHESIZE_PROMPT, parse_hypothesis
from pipeline_sentinel.types import CheckResult, Incident

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


class TriageState(TypedDict):
    """State threaded through the triage graph (one source)."""

    source: str
    failures: list[dict]
    severity: str
    probable_cause: str
    suggested_action: str


def score_severity(failures: list[dict]) -> str:
    """Deterministic severity: the worst applicable rule wins."""
    level = "low"
    for failure in failures:
        name = failure["check"]
        metric = failure.get("metric") or 0.0
        if name == "freshness":
            candidate = "critical"  # data stopped arriving entirely
        elif name == "row_count" and metric > 0.5:
            candidate = "critical"  # volume collapsed
        elif name in ("row_count", "schema_drift"):
            candidate = "high"
        else:
            candidate = "medium"  # quality regressions: nulls, dupes, ranges
        if SEVERITY_RANK[candidate] > SEVERITY_RANK[level]:
            level = candidate
    return level


def build_agent(llm):
    """Compile the per-source triage graph.

    ``llm`` must implement ``invoke(prompt) -> str``.
    """

    def correlate(state: TriageState) -> dict:
        return {"severity": score_severity(state["failures"])}

    def hypothesize(state: TriageState) -> dict:
        rendered = "\n".join(
            f"- {item['check']}: metric={item['metric']}, details={item['details']}"
            for item in state["failures"]
        )
        raw = llm.invoke(HYPOTHESIZE_PROMPT.format(source=state["source"], failures=rendered))
        cause, action = parse_hypothesis(raw)
        return {"probable_cause": cause, "suggested_action": action}

    graph = StateGraph(TriageState)
    graph.add_node("correlate", correlate)
    graph.add_node("hypothesize", hypothesize)
    graph.set_entry_point("correlate")
    graph.add_edge("correlate", "hypothesize")
    graph.add_edge("hypothesize", END)
    return graph.compile()


def triage(failures: list[CheckResult], agent) -> list[Incident]:
    """Group failures by source and triage each group into one incident."""
    by_source: dict[str, list[CheckResult]] = {}
    for failure in failures:
        by_source.setdefault(failure.source, []).append(failure)
    incidents = []
    for source, group in sorted(by_source.items()):
        final = agent.invoke(
            {
                "source": source,
                "failures": [item.to_dict() for item in group],
                "severity": "",
                "probable_cause": "",
                "suggested_action": "",
            }
        )
        check_names = sorted({item.check for item in group})
        stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        incidents.append(
            Incident(
                id=f"INC-{stamp}-{source}",
                source=source,
                severity=final["severity"],
                title=f"{source}: {', '.join(check_names)} failed",
                probable_cause=final["probable_cause"],
                suggested_action=final["suggested_action"],
                failed_checks=[item.check for item in group],
            )
        )
    return incidents
