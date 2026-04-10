"""
/analyze route – the single API endpoint.
"""
from flask import Blueprint, request, jsonify
from services.riot_detector import detect as detect_riot
from services.fake_news_detector import detect as detect_fake
from utils.helpers import log_request, clamp, timestamp_iso

analyze_bp = Blueprint("analyze", __name__)

# ──────────────────────────────────────────────
# Input validation
# ──────────────────────────────────────────────
MIN_LENGTH = 10
MAX_LENGTH = 5000


def _validate(data: dict | None) -> tuple[bool, str]:
    if data is None:
        return False, "Request body must be JSON."
    text = data.get("text", "")
    if not isinstance(text, str) or not text.strip():
        return False, "Field 'text' is required and cannot be empty."
    if len(text.strip()) < MIN_LENGTH:
        return False, f"Text too short. Minimum {MIN_LENGTH} characters required."
    if len(text.strip()) > MAX_LENGTH:
        return False, f"Text too long. Maximum {MAX_LENGTH} characters allowed."
    return True, ""


# ──────────────────────────────────────────────
# Decision Engine
# ──────────────────────────────────────────────
def _combine(riot: dict, fake: dict) -> dict:
    """Merge riot + fake results into a unified response."""

    # Overall confidence = weighted average of sub-scores
    riot_weight = 0.55
    fake_weight = 0.45
    combined_score = (riot["risk_score"] * riot_weight
                      + fake["fake_score"] * fake_weight)
    confidence = clamp(combined_score, 0, 100)

    # Overall risk level
    if riot["risk_level"] == "dangerous" or fake["verdict"] == "fake":
        overall = "high"
    elif riot["risk_level"] == "warning" or fake["verdict"] == "suspicious":
        overall = "medium"
    else:
        overall = "low"

    # Threat category
    categories = []
    if riot["risk_level"] != "safe":
        categories.append("Violence / Riot Incitement")
    if fake["verdict"] != "real":
        categories.append("Misinformation / Fake News")
    if not categories:
        categories.append("Clean Content")

    return {
        "overall_risk": overall,
        "confidence": round(confidence, 1),
        "categories": categories,
    }


# ──────────────────────────────────────────────
# Endpoint
# ──────────────────────────────────────────────
@analyze_bp.route("/analyze", methods=["POST"])
def analyze():
    # 1. Validate
    ok, msg = _validate(request.get_json(silent=True))
    if not ok:
        return jsonify({"success": False, "error": msg}), 400

    text = request.get_json()["text"].strip()

    try:
        # 2. Run detection modules
        riot_result = detect_riot(text)
        fake_result = detect_fake(text)

        # 3. Decision engine
        combined = _combine(riot_result, fake_result)

        # 4. Build response
        response = {
            "success": True,
            "timestamp": timestamp_iso(),
            "input_length": len(text),
            "riot_analysis": riot_result,
            "fake_analysis": fake_result,
            "overall": combined,
        }

        # 5. Log
        log_request(text, response)

        return jsonify(response), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal processing error: {str(e)}"
        }), 500
