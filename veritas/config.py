"""Runtime configuration, loaded from environment / .env."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_key: str
    extract_model: str
    verify_model: str


def load_settings() -> Settings:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key "
            "(get one free at https://aistudio.google.com/apikey)."
        )
    return Settings(
        api_key=api_key,
        # flash-lite has a far more generous free-tier quota than flash/pro,
        # which matters a lot when running without billing enabled.
        extract_model=os.getenv("VERITAS_EXTRACT_MODEL", "gemini-flash-lite-latest").strip(),
        verify_model=os.getenv("VERITAS_VERIFY_MODEL", "gemini-flash-lite-latest").strip(),
    )
