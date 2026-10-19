"""Configuration via environment variables with sane local defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Override any of these with environment variables."""

    sentinel_dir: str = os.environ.get("SENTINEL_DIR", ".sentinel")
    default_db: str = os.environ.get("SENTINEL_DB", "data/demo.db")
    baseline_days: int = int(os.environ.get("SENTINEL_BASELINE_DAYS", "7"))
    volume_threshold_pct: float = float(os.environ.get("SENTINEL_VOLUME_THRESHOLD", "0.3"))
    max_age_hours: float = float(os.environ.get("SENTINEL_MAX_AGE_HOURS", "26"))
    max_null_rate: float = float(os.environ.get("SENTINEL_MAX_NULL_RATE", "0.05"))
    llm_model: str = os.environ.get("SENTINEL_LLM_MODEL", "llama3.1")
    ollama_base_url: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


settings = Settings()
