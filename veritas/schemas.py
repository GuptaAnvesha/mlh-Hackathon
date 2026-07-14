"""Data models shared across the Veritas pipeline."""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    """Outcome of grounding a single claim against live web sources."""

    SUPPORTED = "SUPPORTED"          # Sources clearly back the claim
    DISPUTED = "DISPUTED"            # Sources contradict or challenge the claim
    UNSUPPORTED = "UNSUPPORTED"      # No credible source found either way
    MISLEADING = "MISLEADING"        # Technically true but framed to deceive
    OPINION = "OPINION"              # Not a factual claim; can't be verified


class Claim(BaseModel):
    """An atomic, independently checkable factual assertion pulled from the text."""

    text: str = Field(description="The claim restated as a single self-contained sentence.")
    checkable: bool = Field(
        description="True if this is a verifiable factual claim, False if it is opinion/rhetoric."
    )


class ClaimList(BaseModel):
    """Structured-output wrapper so Gemini can return a typed list of claims."""

    claims: List[Claim]


class VerdictOut(BaseModel):
    """Structured-output shape for an ungrounded verdict (no Search tool)."""

    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str


class Citation(BaseModel):
    """A web source Gemini's grounding tool used to reach a verdict."""

    title: str = ""
    uri: str = ""


class ClaimResult(BaseModel):
    """A fully evaluated claim: verdict, reasoning, confidence, and sources."""

    claim: str
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0, description="0-1 model confidence in the verdict.")
    explanation: str
    citations: List[Citation] = Field(default_factory=list)
    grounded: bool = Field(
        default=True,
        description="True if verified against live web sources; False if grounding was "
        "unavailable and the model's own knowledge was used as a fallback.",
    )


class Report(BaseModel):
    """The final analysis returned to the caller."""

    input_text: str
    credibility_score: int = Field(ge=0, le=100, description="0 (fabricated) to 100 (well-supported).")
    summary: str
    results: List[ClaimResult] = Field(default_factory=list)
