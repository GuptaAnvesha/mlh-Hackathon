"""Orchestrates the full Veritas analysis: extract -> verify -> score."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from .claims import extract_claims
from .schemas import ClaimResult, Report, Verdict
from .verify import verify_claim

# How much each verdict contributes to the overall credibility score.
_VERDICT_WEIGHT = {
    Verdict.SUPPORTED: 1.0,
    Verdict.MISLEADING: 0.3,
    Verdict.UNSUPPORTED: 0.5,
    Verdict.DISPUTED: 0.0,
    Verdict.OPINION: None,  # excluded from scoring
}


def _credibility_score(results: list[ClaimResult]) -> int:
    weighted_sum = 0.0
    weight_total = 0.0
    for r in results:
        base = _VERDICT_WEIGHT.get(r.verdict)
        if base is None:  # opinions don't move the score
            continue
        # Confidence acts as the weight so shaky verdicts count for less.
        w = max(r.confidence, 0.05)
        weighted_sum += base * w
        weight_total += w
    if weight_total == 0:
        return 50  # nothing checkable -> neutral
    return round(100 * weighted_sum / weight_total)


def _summarize(results: list[ClaimResult], score: int) -> str:
    counts: dict[Verdict, int] = {}
    for r in results:
        counts[r.verdict] = counts.get(r.verdict, 0) + 1
    parts = [f"{n} {v.value.lower()}" for v, n in counts.items()]
    breakdown = ", ".join(parts) if parts else "no checkable claims"
    if score >= 75:
        tone = "largely well-supported"
    elif score >= 45:
        tone = "mixed — verify before sharing"
    else:
        tone = "poorly supported; treat with skepticism"

    checkable = [r for r in results if r.verdict != Verdict.OPINION]
    mode = ""
    if checkable and not any(r.grounded for r in checkable):
        mode = " ⚠️ Ungrounded mode (no web sources — enable API billing for live grounding)."
    return f"Credibility {score}/100 — {tone}. Claims: {breakdown}.{mode}"


def analyze(text: str, max_workers: int = 5) -> Report:
    """Run the end-to-end analysis and return a Report."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Input text is empty.")

    claim_list = extract_claims(text)
    checkable = [c.text for c in claim_list.claims if c.checkable]

    results: list[ClaimResult] = []
    if checkable:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            results = list(pool.map(verify_claim, checkable))

    # Preserve any opinion claims in the report so the user sees them flagged.
    for c in claim_list.claims:
        if not c.checkable:
            results.append(
                ClaimResult(
                    claim=c.text,
                    verdict=Verdict.OPINION,
                    confidence=1.0,
                    explanation="Flagged as opinion or rhetoric — not a checkable fact.",
                )
            )

    score = _credibility_score(results)
    return Report(
        input_text=text,
        credibility_score=score,
        summary=_summarize(results, score),
        results=results,
    )
