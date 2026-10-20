"""Eval harness: inject synthetic anomalies, measure detection. Milestone M5."""

from pipeline_sentinel.eval.cases import EVAL_CASES
from pipeline_sentinel.eval.run import CaseResult, run_eval

__all__ = ["EVAL_CASES", "CaseResult", "run_eval"]
