"""Triage prompts and structured-output parsing."""

from __future__ import annotations

import re

HYPOTHESIZE_PROMPT = """You are a data-incident analyst. Given the failed data quality checks for one source, write the most probable cause and a suggested next action.

Source: {source}

Failed checks:
{failures}

Rules:
- Base the cause ONLY on the failed checks shown. Do not invent other symptoms.
- One or two sentences per field, plain language.
- End with exactly these two lines:
PROBABLE_CAUSE: <text>
SUGGESTED_ACTION: <text>
"""

_CAUSE_RE = re.compile(r"^PROBABLE_CAUSE:\s*(.+)$", re.MULTILINE)
_ACTION_RE = re.compile(r"^SUGGESTED_ACTION:\s*(.+)$", re.MULTILINE)


def parse_hypothesis(raw: str) -> tuple[str, str]:
    """Extract (probable_cause, suggested_action) from the LLM output.

    Falls back to the raw text as the cause when the model does not follow
    the format, so no signal is ever lost.
    """
    cause_match = _CAUSE_RE.search(raw)
    action_match = _ACTION_RE.search(raw)
    cause = cause_match.group(1).strip() if cause_match else raw.strip()[:500]
    action = (
        action_match.group(1).strip() if action_match else "Investigate the failed checks manually."
    )
    return (cause or "No hypothesis produced.", action)
