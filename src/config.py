from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    data_dir: str
    checkpoint_db: str


def load_settings() -> Settings:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-nano").strip()
    data_dir = os.getenv("SCAM_TRIAGE_DATA_DIR", "data").strip()
    checkpoint_db = os.getenv("SCAM_TRIAGE_CHECKPOINT_DB", ".scam_triage/checkpoints.sqlite").strip()
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Export it in your shell or add it to .env"
        )
    return Settings(
        openai_api_key=api_key,
        openai_model=model,
        data_dir=data_dir,
        checkpoint_db=checkpoint_db,
    )
