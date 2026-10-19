"""Tests for the triage agent (LLM is faked)."""

from __future__ import annotations

from pipeline_sentinel.triage import build_agent, score_severity, triage
from pipeline_sentinel.triage.prompts import parse_hypothesis
from pipeline_sentinel.types import CheckResult


class FakeLLM:
    def __init__(self, reply: str):
        self.reply = reply
        self.prompts: list[str] = []

    def invoke(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.reply


def _failure(source: str = "feed_a", check: str = "row_count", metric: float = 0.6):
    return CheckResult(source=source, check=check, passed=False, metric=metric)


def test_score_severity_rules():
    assert score_severity([{"check": "freshness", "metric": 48.0}]) == "critical"
    assert score_severity([{"check": "row_count", "metric": 0.6}]) == "critical"
    assert score_severity([{"check": "row_count", "metric": 0.35}]) == "high"
    assert score_severity([{"check": "schema_drift", "metric": 2.0}]) == "high"
    assert score_severity([{"check": "null_rate", "metric": 0.2}]) == "medium"
    # worst rule wins
    assert (
        score_severity(
            [
                {"check": "null_rate", "metric": 0.2},
                {"check": "freshness", "metric": 48.0},
            ]
        )
        == "critical"
    )


def test_parse_hypothesis():
    raw = (
        "Some thinking.\nPROBABLE_CAUSE: Upstream job failed.\nSUGGESTED_ACTION: Re-run the loader."
    )
    cause, action = parse_hypothesis(raw)
    assert cause == "Upstream job failed."
    assert action == "Re-run the loader."


def test_parse_hypothesis_falls_back_to_raw_text():
    cause, action = parse_hypothesis("no structure here")
    assert cause == "no structure here"
    assert "manually" in action


def test_triage_builds_one_incident_per_source():
    llm = FakeLLM("PROBABLE_CAUSE: Load job crashed.\nSUGGESTED_ACTION: Restart the loader.")
    agent = build_agent(llm)
    failures = [
        _failure("feed_a", "row_count", 0.6),
        _failure("feed_a", "freshness", 48.0),
        _failure("feed_b", "null_rate", 0.2),
    ]
    incidents = triage(failures, agent)
    assert len(incidents) == 2
    by_source = {incident.source: incident for incident in incidents}
    assert by_source["feed_a"].severity == "critical"
    assert by_source["feed_b"].severity == "medium"
    assert "row_count" in by_source["feed_a"].title
    assert by_source["feed_a"].probable_cause == "Load job crashed."
    assert by_source["feed_a"].suggested_action == "Restart the loader."
    assert by_source["feed_a"].id.startswith("INC-")
    assert by_source["feed_a"].failed_checks == ["row_count", "freshness"]
    # the agent saw the check details
    assert "row_count" in llm.prompts[0]
    assert "feed_a" in llm.prompts[0]


def test_triage_no_failures_returns_empty():
    agent = build_agent(FakeLLM("unused"))
    assert triage([], agent) == []
