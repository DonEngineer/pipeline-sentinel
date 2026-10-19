"""LLM triage agent: correlate failed checks into incidents. Milestone M3."""

from pipeline_sentinel.triage.agent import build_agent, score_severity, triage
from pipeline_sentinel.triage.llm import OllamaChat

__all__ = ["OllamaChat", "build_agent", "score_severity", "triage"]
