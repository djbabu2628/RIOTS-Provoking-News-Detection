"""
Fake News Detection Module
────────────────────────────
Detects suspicious, clickbait, or fabricated content
using keyword heuristics, pattern matching, and claim analysis.
"""
from __future__ import annotations
import re
from utils.helpers import clean_text, word_list, clamp

# ──────────────────────────────────────────────
# Suspicious / clickbait indicators (weighted)
# ──────────────────────────────────────────────
CLICKBAIT_WORDS: dict[str, float] = {
    "shocking": 6, "unbelievable": 6, "you won't believe": 8,
    "mind-blowing": 6, "jaw-dropping": 6, "breaking": 4,
    "exclusive": 5, "exposed": 5, "secret": 5, "revealed": 5,
    "urgent": 5, "alert": 4, "warning": 4,
    "must see": 6, "must watch": 6, "must read": 6,
    "gone wrong": 5, "gone viral": 5, "what happened next": 7,
    "number 5 will shock you": 8, "doctors hate": 7,
    "one weird trick": 8, "they don't want you to know": 8,
    "before it's deleted": 7, "share before banned": 8,
    "100% true": 7, "100% real": 7, "100% proof": 7,
}

FAKE_PATTERNS: dict[str, float] = {
    "sources say": 4, "anonymous sources": 5, "unnamed sources": 5,
    "people are saying": 5, "everyone knows": 5, "it is well known": 4,
    "many experts": 4, "some scientists": 4,
    "exposed the truth": 6, "mainstream media won't tell you": 7,
    "government hiding": 6, "cover up": 6, "conspiracy": 5,
    "big pharma": 5, "wake up": 4, "open your eyes": 5,
    "do your research": 5, "think about it": 3, "connect the dots": 5,
    "just asking questions": 4,
}

CREDIBILITY_BOOSTERS: set[str] = {
    "according to", "study published", "peer reviewed",
    "university", "research shows", "data indicates",
    "official statement", "press release",
    "reuters", "associated press", "bbc", "verified",
}

# Exclamation / ALL-CAPS heuristics
MAX_CAPS_RATIO = 0.35          # >35% caps → suspicious
MAX_EXCLAMATION_RATIO = 0.05   # >5% exclamation marks → suspicious


# ──────────────────────────────────────────────
# Core detection
# ──────────────────────────────────────────────
def _clickbait_score(text: str) -> tuple[float, list[str]]:
    cleaned = clean_text(text)
    score = 0.0
    matched = []
    for phrase, weight in CLICKBAIT_WORDS.items():
        if phrase in cleaned:
            score += weight
            matched.append(phrase)
    return score, matched


def _fake_pattern_score(text: str) -> tuple[float, list[str]]:
    cleaned = clean_text(text)
    score = 0.0
    matched = []
    for phrase, weight in FAKE_PATTERNS.items():
        if phrase in cleaned:
            score += weight
            matched.append(phrase)
    return score, matched


def _style_score(text: str) -> float:
    """Penalise ALL-CAPS and excessive punctuation."""
    if not text:
        return 0
    alpha = [c for c in text if c.isalpha()]
    if not alpha:
        return 0
    caps_ratio = sum(1 for c in alpha if c.isupper()) / len(alpha)
    excl_ratio = text.count("!") / len(text)

    score = 0.0
    if caps_ratio > MAX_CAPS_RATIO:
        score += (caps_ratio - MAX_CAPS_RATIO) * 40
    if excl_ratio > MAX_EXCLAMATION_RATIO:
        score += (excl_ratio - MAX_EXCLAMATION_RATIO) * 80
    return score


def _credibility_damper(text: str) -> float:
    cleaned = clean_text(text)
    hits = sum(1 for b in CREDIBILITY_BOOSTERS if b in cleaned)
    if hits >= 3:
        return 0.4
    elif hits >= 1:
        return 0.7
    return 1.0


def _claim_density(text: str) -> float:
    """Penalise texts with lots of numbers/stats (often fabricated)."""
    numbers = re.findall(r"\d+%|\d{4,}", text)
    if len(numbers) > 5:
        return 8
    elif len(numbers) > 2:
        return 4
    return 0


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────
def detect(text: str) -> dict:
    """
    Analyse text for fake-news indicators.

    Returns
    -------
    dict  with keys:
        verdict       : "fake" | "real" | "suspicious"
        fake_score    : 0 – 100
        clickbait     : list[str]
        patterns      : list[str]
        details       : str
    """
    cb_score, cb_matched = _clickbait_score(text)
    fp_score, fp_matched = _fake_pattern_score(text)
    style = _style_score(text)
    claims = _claim_density(text)

    raw = (cb_score + fp_score + style + claims) * _credibility_damper(text)
    normalised = clamp(raw * 4.0, 0, 100)

    if normalised >= 60:
        verdict = "fake"
        detail = "🚨 High probability of fake / misleading content. Multiple red flags detected."
    elif normalised >= 30:
        verdict = "suspicious"
        detail = "🔍 Content has some suspicious markers. Verify with trusted sources."
    else:
        verdict = "real"
        detail = "✅ Content appears credible. No significant fake-news indicators found."

    return {
        "verdict": verdict,
        "fake_score": round(normalised, 1),
        "clickbait": cb_matched,
        "patterns": fp_matched,
        "details": detail,
    }
