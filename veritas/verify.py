"""Step 2 of the pipeline: verify a single claim against live web sources.

This is the heart of Veritas. We give Gemini the Google Search *grounding*
tool so it checks the claim against the real web rather than its own memory,
then we read the citations back out of the response's grounding metadata.

Note: Gemini can't combine the grounding tool with JSON `response_schema` in
one call, so we ask for a fenced JSON verdict block inside the grounded text
answer and parse it out, while pulling citations from grounding_metadata.
"""

from __future__ import annotations

import json
import re

from google.genai import errors, types

from .config import load_settings
from .gemini_client import get_client
from .schemas import Citation, ClaimResult, Verdict, VerdictOut

_UNGROUNDED_NOTE = " (Verified from model knowledge — enable API billing for live web sources.)"

_UNGROUNDED_PROMPT = """Fact-check this claim using your own knowledge.

CLAIM: "{claim}"

Choose a verdict: SUPPORTED, DISPUTED, MISLEADING (literally true but deceptively
framed), UNSUPPORTED (can't confirm or deny), or OPINION (not a checkable fact).
Give a confidence from 0 to 1 and a one or two sentence explanation."""

_VERIFY_PROMPT = """Fact-check the following claim using web search.

CLAIM: "{claim}"

Search for authoritative, up-to-date sources. Then decide a verdict:
- SUPPORTED: credible sources clearly confirm the claim.
- DISPUTED: credible sources contradict the claim.
- MISLEADING: literally true but framed to create a false impression.
- UNSUPPORTED: no credible source confirms or denies it.
- OPINION: not a checkable factual claim.

Respond with a short analysis, then end your message with EXACTLY one JSON
object in a ```json code block, and nothing after it:

```json
{{"verdict": "SUPPORTED", "confidence": 0.0, "explanation": "one or two sentences"}}
```
Confidence is a number from 0 to 1."""

_JSON_BLOCK = re.compile(r"```json\s*(\{.*?\})\s*```", re.DOTALL)


def _extract_citations(response) -> list[Citation]:
    citations: list[Citation] = []
    seen: set[str] = set()
    for candidate in getattr(response, "candidates", None) or []:
        meta = getattr(candidate, "grounding_metadata", None)
        if not meta:
            continue
        for chunk in getattr(meta, "grounding_chunks", None) or []:
            web = getattr(chunk, "web", None)
            if not web:
                continue
            uri = getattr(web, "uri", "") or ""
            if uri and uri not in seen:
                seen.add(uri)
                citations.append(Citation(title=getattr(web, "title", "") or "", uri=uri))
    return citations


def _parse_verdict(text: str) -> tuple[Verdict, float, str]:
    match = _JSON_BLOCK.search(text or "")
    raw = match.group(1) if match else None
    if raw is None:
        # Last-ditch: grab the first {...} we can find.
        brace = re.search(r"\{.*\}", text or "", re.DOTALL)
        raw = brace.group(0) if brace else None
    if raw:
        try:
            data = json.loads(raw)
            verdict = Verdict(str(data.get("verdict", "UNSUPPORTED")).upper())
            confidence = float(data.get("confidence", 0.5))
            explanation = str(data.get("explanation", "")).strip()
            return verdict, max(0.0, min(1.0, confidence)), explanation
        except (ValueError, KeyError):
            pass
    return Verdict.UNSUPPORTED, 0.3, (text or "No verdict could be parsed.").strip()[:400]


def _verify_grounded(client, model, claim) -> ClaimResult:
    """Verify against live web sources. Parsing is text-based because the Search
    tool cannot be combined with JSON response_schema in one call."""
    response = client.models.generate_content(
        model=model,
        contents=_VERIFY_PROMPT.format(claim=claim),
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.0,
        ),
    )
    verdict, confidence, explanation = _parse_verdict(response.text)
    return ClaimResult(
        claim=claim,
        verdict=verdict,
        confidence=confidence,
        explanation=explanation or "No explanation provided.",
        citations=_extract_citations(response),
        grounded=True,
    )


def _verify_ungrounded(client, model, claim) -> ClaimResult:
    """Fallback verification from model knowledge. With no Search tool we can use
    structured output for a reliable, always-parseable verdict."""
    response = client.models.generate_content(
        model=model,
        contents=_UNGROUNDED_PROMPT.format(claim=claim),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=VerdictOut,
            temperature=0.0,
        ),
    )
    parsed = response.parsed
    if not isinstance(parsed, VerdictOut):
        parsed = VerdictOut.model_validate_json(response.text)
    return ClaimResult(
        claim=claim,
        verdict=parsed.verdict,
        confidence=parsed.confidence,
        explanation=(parsed.explanation or "No explanation provided.") + _UNGROUNDED_NOTE,
        citations=[],
        grounded=False,
    )


def verify_claim(claim: str) -> ClaimResult:
    """Verify a claim against the web, falling back to model knowledge if grounding is unavailable.

    The Google Search grounding tool requires a billing-enabled key. On the free
    tier it returns HTTP 429, so we retry once without the tool (using structured
    output) and clearly mark the result as ungrounded rather than failing.
    """
    settings = load_settings()
    client = get_client()
    try:
        return _verify_grounded(client, settings.verify_model, claim)
    except errors.ClientError as exc:
        if getattr(exc, "code", None) != 429:
            raise
        # Grounding quota unavailable: fall back to ungrounded verification.

    try:
        return _verify_ungrounded(client, settings.verify_model, claim)
    except errors.ClientError as exc:
        if getattr(exc, "code", None) != 429:
            raise
        # Even the free-tier text quota is exhausted: don't crash the whole
        # report — return a clearly-labelled placeholder for this one claim.
        return ClaimResult(
            claim=claim,
            verdict=Verdict.UNSUPPORTED,
            confidence=0.0,
            explanation="Rate limited by the Gemini free tier — couldn't verify this claim. "
            "Wait for the daily quota to reset, or enable API billing.",
            citations=[],
            grounded=False,
        )
