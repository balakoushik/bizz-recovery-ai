from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.database import db
from models.project import Project
from models.risk import Risk, RiskHistory
from services.risk_engine import analyze_project
from services.analytics_engine import calculate_health_scores

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("/projects")
def list_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("projects.html", projects=projects)


@projects_bp.route("/projects/new", methods=["POST"])
def create_project():
    def f(name, default=0):
        val = request.form.get(name, "")
        try:
            return float(val) if val != "" else default
        except ValueError:
            return default

    def parse_date(name, default_days=0):
        val = request.form.get(name, "")
        try:
            return datetime.strptime(val, "%Y-%m-%d")
        except (ValueError, TypeError):
            return datetime.utcnow()

    project = Project(
        name=request.form.get("name", "Untitled Project").strip() or "Untitled Project",
        description=request.form.get("description", ""),
        industry=request.form.get("industry", "Software"),
        budget=f("budget", 100000),
        current_spending=f("current_spending", 0),
        start_date=parse_date("start_date"),
        expected_end_date=parse_date("expected_end_date"),
        progress=f("progress", 0),
        expected_progress=f("expected_progress", 0),
        team_size=int(f("team_size", 1)),
        tech_stack=request.form.get("tech_stack", ""),
        infrastructure_type=request.form.get("infrastructure_type", "Cloud"),
        status=request.form.get("status", "In Progress"),
        cpu_utilization=f("cpu_utilization", 40),
        memory_utilization=f("memory_utilization", 40),
        storage_utilization=f("storage_utilization", 40),
        network_utilization=f("network_utilization", 40),
        server_availability=f("server_availability", 99.5),
        security_incidents=int(f("security_incidents", 0)),
        customer_satisfaction=f("customer_satisfaction", 75),
        unresolved_issues=int(f("unresolved_issues", 0)),
        dependency_delays=int(f("dependency_delays", 0)),
    )
    db.session.add(project)
    db.session.commit()

    # Immediately run risk analysis for the new project
    risks = analyze_project(project)
    for r in risks:
        db.session.add(r)
    db.session.commit()

    health = calculate_health_scores(project)
    db.session.add(RiskHistory(project_id=project.id, risk_score=health["overall_risk_score"],
                                health_score=health["overall_health"]))
    db.session.commit()

    flash(f'Project "{project.name}" created and analyzed successfully.', "success")
    return redirect(url_for("projects.project_detail", project_id=project.id))


@projects_bp.route("/projects/<int:project_id>")
def project_detail(project_id):
    project = Project.query.get_or_404(project_id)
    risks = Risk.query.filter_by(project_id=project.id).order_by(Risk.risk_score.desc()).all()
    health = calculate_health_scores(project)
    return render_template("project_detail.html", project=project, risks=risks, health=health)


@projects_bp.route("/projects/<int:project_id>/delete", methods=["POST"])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash("Project deleted.", "info")
    return redirect(url_for("projects.list_projects"))
