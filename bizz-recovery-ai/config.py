"""
Application configuration.
Reads settings from environment variables (via .env) with sane defaults
so the app runs out-of-the-box with zero configuration.
"""
import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "bizz-recovery-ai-dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'bizz_recovery.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() in ("1", "true", "yes")

    # Optional external LLM integration. Empty string == LOCAL INTELLIGENCE MODE.
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    # Risk classification thresholds (0-100 risk score scale)
    RISK_THRESHOLDS = {
        "LOW": (0, 24),
        "MEDIUM": (25, 49),
        "HIGH": (50, 74),
        "CRITICAL": (75, 100),
    }

    RISK_CATEGORIES = [
        "TECHNICAL", "FINANCIAL", "SECURITY", "OPERATIONAL", "RESOURCE",
        "SCHEDULE", "MARKET", "CUSTOMER", "COMPLIANCE", "INFRASTRUCTURE",
        "SUPPLY CHAIN", "REPUTATIONAL",
    ]
