"""
Riot / Violence Detection Module
─────────────────────────────────
Detects violence-inciting, hateful, or aggressive language
using keyword matching, sentiment heuristics, and risk scoring.
"""
from __future__ import annotations
import re
from utils.helpers import clean_text, word_list, clamp

# ──────────────────────────────────────────────
# Keyword dictionaries (weighted)
# ──────────────────────────────────────────────
VIOLENCE_KEYWORDS: dict[str, float] = {
    # Direct violence
    "kill": 8, "murder": 9, "attack": 7, "bomb": 9, "riot": 8,
    "destroy": 7, "burn": 6, "shoot": 8, "stab": 8, "assault": 7,
    "explode": 8, "terrorist": 9, "terrorism": 9, "massacre": 9,
    "slaughter": 9, "execute": 7, "behead": 9, "lynch": 9,
    "genocide": 10, "war": 5, "weapon": 6, "gun": 6, "knife": 5,
    "bloodshed": 8, "carnage": 8, "rampage": 7, "arson": 7,

    # Incitement
    "revolt": 6, "uprising": 6, "overthrow": 7, "rebellion": 6,
    "insurrection": 7, "coup": 7, "militant": 7, "extremist": 7,
    "radicalize": 7, "jihad": 8, "martyr": 6,

    # Hate speech
    "hate": 5, "racist": 6, "bigot": 5, "supremacist": 7,
    "ethnic cleansing": 10, "xenophob": 6, "discriminat": 5,
}

AGGRESSIVE_PHRASES: dict[str, float] = {
    "death to": 9, "wipe out": 8, "blow up": 8,
    "set fire": 7, "take revenge": 7, "must die": 9,
    "blood will flow": 9, "raise arms": 7, "pick up weapons": 8,
    "burn down": 7, "tear apart": 6, "no mercy": 6,
    "fight back": 4, "stand up against": 3, "take to streets": 5,
}

# Sentiment modifiers
NEGATIVE_MODIFIERS: dict[str, float] = {
    "should": 1.3, "must": 1.4, "need to": 1.3,
    "going to": 1.2, "will": 1.1, "let's": 1.3,
    "everybody": 1.2, "everyone": 1.2, "all of us": 1.2,
}

POSITIVE_DAMPERS: set[str] = {
    "peace", "peaceful", "calm", "love", "unity",
    "together", "harmony", "nonviolent", "protest peacefully",
    "dialogue", "negotiate", "resolve",
}


# ──────────────────────────────────────────────
# Core detection
# ──────────────────────────────────────────────
def _keyword_score(text: str) -> tuple[float, list[str]]:
    """Score based on individual violence keywords found."""
    words = word_list(text)
    score = 0.0
    matched = []
    for kw, weight in VIOLENCE_KEYWORDS.items():
        if kw in words or re.search(rf'\b{re.escape(kw)}\b', text, re.IGNORECASE):
            score += weight
            matched.append(kw)
    return score, matched


def _phrase_score(text: str) -> tuple[float, list[str]]:
    """Score based on aggressive phrases."""
    cleaned = clean_text(text)
    score = 0.0
    matched = []
    for phrase, weight in AGGRESSIVE_PHRASES.items():
        if phrase in cleaned:
            score += weight
            matched.append(phrase)
    return score, matched


def _sentiment_modifier(text: str) -> float:
    """Multiplier based on call-to-action / urgency modifiers."""
    cleaned = clean_text(text)
    multiplier = 1.0
    for mod, factor in NEGATIVE_MODIFIERS.items():
        if mod in cleaned:
            multiplier *= factor
    # Cap the multiplier
    return min(multiplier, 3.0)


def _peace_damper(text: str) -> float:
    """Reduce score if peaceful language is present."""
    words = set(word_list(text))
    overlap = words & POSITIVE_DAMPERS
    if len(overlap) >= 3:
        return 0.4
    elif len(overlap) >= 1:
        return 0.7
    return 1.0


# ──────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────
def detect(text: str) -> dict:
    """
    Analyse text for riot / violence risk.

    Returns
    -------
    dict  with keys:
        risk_level   : "safe" | "warning" | "dangerous"
        risk_score   : 0 – 100
        keywords_found : list[str]
        phrases_found  : list[str]
        details        : str
    """
    kw_score, kw_matched = _keyword_score(text)
    ph_score, ph_matched = _phrase_score(text)

    raw = (kw_score + ph_score) * _sentiment_modifier(text) * _peace_damper(text)
    # Normalise to 0-100  (rough cap at raw ~50 → 100)
    normalised = clamp(raw * 2, 0, 100)

    if normalised >= 65:
        level = "dangerous"
        detail = "⚠️ High violence / riot risk detected. Content contains aggressive or hateful language."
    elif normalised >= 30:
        level = "warning"
        detail = "⚡ Moderate risk detected. Some aggressive keywords or tones found."
    else:
        level = "safe"
        detail = "✅ Content appears safe with no significant violent indicators."

    return {
        "risk_level": level,
        "risk_score": round(normalised, 1),
        "keywords_found": kw_matched,
        "phrases_found": ph_matched,
        "details": detail,
    }
