"""
AI News Analyzer – Flask Backend
=================================
Main application entry point.
"""

import os 
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

    # Root route — welcome page
    @app.route("/", methods=["GET"])
    def index():
        return """
        <html><head><title>AI News Analyzer API</title>
        <style>
            body { font-family: sans-serif; background: #0a0a0f; color: #e8e8ef;
                   display: flex; align-items: center; justify-content: center;
                   min-height: 100vh; margin: 0; }
            .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 16px; padding: 40px 48px; text-align: center; max-width: 480px; }
            h1 { font-size: 28px; margin-bottom: 8px; }
            .badge { background: rgba(81,207,102,0.15); color: #51cf66;
                     border: 1px solid rgba(81,207,102,0.3); border-radius: 100px;
                     display: inline-block; padding: 4px 16px; font-size: 13px;
                     font-weight: 600; margin-bottom: 20px; }
            code { background: rgba(255,255,255,0.08); padding: 2px 8px;
                   border-radius: 6px; font-size: 14px; }
            p { color: #8b8b9e; font-size: 15px; line-height: 1.6; }
        </style></head>
        <body><div class="card">
            <div class="badge">✅ API Online</div>
            <h1>🛡️ AI News Analyzer</h1>
            <p>Backend is running successfully.<br>
               Use <code>POST /api/analyze</code> to analyze text.<br>
               Use <code>GET /api/health</code> for health check.</p>
        </div></body></html>
        """, 200

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

app = create_app()
# ──────────────────────────────────────────────
# Run
# ──────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
