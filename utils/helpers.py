"""
Utility helpers for the AI News Analyzer backend.
"""
import re
import logging
from datetime import datetime, timezone

# ──────────────────────────────────────────────
# Logging setup
# ──────────────────────────────────────────────
LOG_FILE = "analyzer.log"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("analyzer")


def log_request(text: str, result: dict) -> None:
    """Log every analysis request for debugging / audit."""
    logger.info("INPUT: %s", text[:200])
    logger.info("OUTPUT: %s", result)


# ──────────────────────────────────────────────
# Text cleaning
# ──────────────────────────────────────────────
def clean_text(text: str) -> str:
    """Lowercase, strip extra whitespace & special chars."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s.,!?'\"-]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def word_list(text: str) -> list[str]:
    """Return list of words from cleaned text."""
    return clean_text(text).split()


# ──────────────────────────────────────────────
# Scoring helpers
# ──────────────────────────────────────────────
def clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def timestamp_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"
