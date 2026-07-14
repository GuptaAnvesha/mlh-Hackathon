"""Step 1 of the pipeline: decompose free text into atomic, checkable claims.

Uses Gemini structured output (response_schema) so we get a typed list back
instead of having to parse prose.
"""

from __future__ import annotations

from google.genai import types

from .config import load_settings
from .gemini_client import get_client
from .schemas import ClaimList

_SYSTEM_INSTRUCTION = """You are a meticulous fact-checking analyst.
Break the user's text into atomic, self-contained factual claims.

Rules:
- Each claim must stand alone (resolve pronouns; include who/what/when).
- One assertion per claim. Split compound sentences.
- Mark opinions, predictions, and rhetorical statements as checkable=false.
- Mark concrete, verifiable statements of fact as checkable=true.
- Do not invent claims that are not present in the text.
- Return at most 12 of the most consequential claims."""


def extract_claims(text: str) -> ClaimList:
    """Return the structured list of claims found in ``text``."""
    settings = load_settings()
    client = get_client()

    response = client.models.generate_content(
        model=settings.extract_model,
        contents=text,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=ClaimList,
            temperature=0.1,
        ),
    )

    parsed = response.parsed
    if isinstance(parsed, ClaimList):
        return parsed
    # Fallback: validate raw JSON text if the SDK didn't auto-parse.
    return ClaimList.model_validate_json(response.text)
