"""Thin wrapper around the google-genai client."""

from __future__ import annotations

from functools import lru_cache

from google import genai

from .config import load_settings


@lru_cache(maxsize=1)
def get_client() -> genai.Client:
    """Return a cached Gemini client authenticated from settings."""
    settings = load_settings()
    return genai.Client(api_key=settings.api_key)
