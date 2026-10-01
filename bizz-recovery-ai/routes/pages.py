from flask import Blueprint, render_template, request, current_app
from models.project import Project
from models.risk import Risk
from services.analytics_engine import calculate_health_scores, generate_warnings
from services.prediction_engine import get_model_status

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/ai-assistant")
def ai_assistant():
    projects = Project.query.all()
    project_id = request.args.get("project_id", type=int)
    selected = None
    if projects:
        selected = Project.query.get(project_id) if project_id else projects[0]
    llm_mode = "External LLM (Claude)" if current_app.config.get("ANTHROPIC_API_KEY") else "Local Intelligence Mode"
    return render_template("ai_assistant.html", projects=projects, selected=selected, llm_mode=llm_mode)


@pages_bp.route("/reports")
def reports():
    projects = Project.query.all()
    project_id = request.args.get("project_id", type=int)
    selected = None
    health = None
    risks = []
    warnings = []
    if projects:
        selected = Project.query.get(project_id) if project_id else projects[0]
        health = calculate_health_scores(selected)
        risks = Risk.query.filter_by(project_id=selected.id).order_by(Risk.risk_score.desc()).all()
        warnings = generate_warnings(selected)
    return render_template("reports.html", projects=projects, selected=selected,
                            health=health, risks=risks, warnings=warnings)


@pages_bp.route("/analytics")
def analytics():
    projects = Project.query.all()
    model_status = get_model_status()
    return render_template("dashboard.html", projects=projects, is_analytics=True, model_status=model_status)


@pages_bp.route("/settings")
def settings():
    llm_configured = bool(current_app.config.get("ANTHROPIC_API_KEY"))
    return render_template("settings.html", llm_configured=llm_configured)
