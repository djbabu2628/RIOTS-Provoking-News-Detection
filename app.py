"""
AI News Analyzer – Flask Backend
=================================
Main application entry point.
"""
from flask import Flask, jsonify
from flask_cors import CORS
from routes.analyze import analyze_bp

# ──────────────────────────────────────────────
# App factory
# ──────────────────────────────────────────────
def create_app() -> Flask:
    app = Flask(__name__)

    # CORS – allow frontend to connect
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Register blueprints
    app.register_blueprint(analyze_bp, url_prefix="/api")

    # Health check
    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "AI News Analyzer"}), 200

    # Global error handlers
    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"success": False, "error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify({"success": False, "error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def internal_error(_):
        return jsonify({"success": False, "error": "Internal server error."}), 500

    return app


# ──────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────
if __name__ == "__name__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
