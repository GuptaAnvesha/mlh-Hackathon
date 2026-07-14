"""Offline tests for the scoring/summary logic (no Gemini API calls)."""

from veritas.pipeline import _credibility_score, _summarize
from veritas.schemas import ClaimResult, Verdict


def _r(verdict: Verdict, confidence: float = 0.9) -> ClaimResult:
    return ClaimResult(claim="c", verdict=verdict, confidence=confidence, explanation="e")


def test_all_supported_scores_high():
    results = [_r(Verdict.SUPPORTED), _r(Verdict.SUPPORTED)]
    assert _credibility_score(results) == 100


def test_all_disputed_scores_zero():
    results = [_r(Verdict.DISPUTED), _r(Verdict.DISPUTED)]
    assert _credibility_score(results) == 0


def test_opinions_are_excluded():
    # Only opinions -> nothing checkable -> neutral 50.
    assert _credibility_score([_r(Verdict.OPINION)]) == 50


def test_mixed_is_between():
    results = [_r(Verdict.SUPPORTED), _r(Verdict.DISPUTED)]
    score = _credibility_score(results)
    assert 0 < score < 100


def test_confidence_weights_the_score():
    strong_true = [_r(Verdict.SUPPORTED, 0.99), _r(Verdict.DISPUTED, 0.10)]
    # High-confidence SUPPORTED should dominate a low-confidence DISPUTED.
    assert _credibility_score(strong_true) > 50


def test_summary_mentions_score():
    results = [_r(Verdict.SUPPORTED)]
    assert "100" in _summarize(results, 100)
