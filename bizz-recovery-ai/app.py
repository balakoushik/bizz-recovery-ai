"""
Bizz Recovery AI — AI-Powered Business & Project Risk Prediction,
Prevention and Recovery Platform.

Run with:
    python app.py

Then open:
    http://127.0.0.1:5000
"""
import os
import threading
import webbrowser

from flask import Flask, render_template

from config import Config
from database.database import db, init_db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Register blueprints
    from routes.dashboard import dashboard_bp
    from routes.projects import projects_bp
    from routes.risks import risks_bp
    from routes.recovery import recovery_bp
    from routes.pages import pages_bp
    from routes.api import api_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(risks_bp)
    app.register_blueprint(recovery_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)

    # Ensure DB exists + seed sample data on first run
    init_db(app)

    # ---- Error handlers so the app never crashes ungracefully ----
    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("error.html", code=500, message="Something went wrong on our end."), 500

    return app


app = create_app()


def _open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")


if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        threading.Timer(1.25, _open_browser).start()
    app.run(host="127.0.0.1", port=5000, debug=app.config.get("DEBUG", True))
