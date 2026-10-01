from flask import Blueprint, render_template, request, redirect, url_for, flash
from database.database import db
from models.project import Project
from models.risk import Risk
from models.recovery import RecoveryPlan
from services.recovery_engine import generate_recovery_plan

recovery_bp = Blueprint("recovery", __name__)


@recovery_bp.route("/recovery-plans")
def list_plans():
    projects = Project.query.all()
    plans = RecoveryPlan.query.order_by(RecoveryPlan.created_at.desc()).all()
    return render_template("recovery_plan.html", projects=projects, plans=plans, active_plan=None)


@recovery_bp.route("/recovery-plans/generate/<int:project_id>", methods=["POST"])
def generate(project_id):
    project = Project.query.get_or_404(project_id)
    risks = Risk.query.filter_by(project_id=project.id).all()
    content = generate_recovery_plan(project, risks)

    plan = RecoveryPlan(project_id=project.id, title=f"Recovery Plan – {project.name}")
    plan.content = content
    db.session.add(plan)
    db.session.commit()
    flash("Recovery plan generated.", "success")
    return redirect(url_for("recovery.view_plan", plan_id=plan.id))


@recovery_bp.route("/recovery-plans/<int:plan_id>")
def view_plan(plan_id):
    plan = RecoveryPlan.query.get_or_404(plan_id)
    projects = Project.query.all()
    plans = RecoveryPlan.query.order_by(RecoveryPlan.created_at.desc()).all()
    return render_template("recovery_plan.html", projects=projects, plans=plans, active_plan=plan)


@recovery_bp.route("/what-if")
def what_if():
    projects = Project.query.all()
    project_id = request.args.get("project_id", type=int)
    selected = None
    if projects:
        selected = Project.query.get(project_id) if project_id else projects[0]
    return render_template("what_if.html", projects=projects, selected=selected)
