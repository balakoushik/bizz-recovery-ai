from datetime import datetime
from flask import Blueprint, jsonify, request
from database.database import db
from models.project import Project
from models.risk import Risk, RiskHistory, Alert
from models.recovery import RecoveryPlan
from services.risk_engine import analyze_project, classify_severity
from services.prediction_engine import predict_project_risk, get_model_status
from services.recovery_engine import generate_recovery_plan
from services.analytics_engine import calculate_health_scores, generate_warnings
from services.ai_engine import answer_question

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------- PROJECTS
@api_bp.route("/projects", methods=["GET"])
def api_list_projects():
    projects = Project.query.order_by(Project.created_at.desc()).all()
    return jsonify([p.to_dict() for p in projects])


@api_bp.route("/projects", methods=["POST"])
def api_create_project():
    data = request.get_json(force=True, silent=True) or {}
    if not data.get("name"):
        return jsonify({"error": "Field 'name' is required."}), 400
    try:
        project = Project(
            name=data.get("name"),
            description=data.get("description", ""),
            industry=data.get("industry", "Software"),
            budget=float(data.get("budget", 100000) or 0),
            current_spending=float(data.get("current_spending", 0) or 0),
            progress=float(data.get("progress", 0) or 0),
            expected_progress=float(data.get("expected_progress", 0) or 0),
            team_size=int(data.get("team_size", 1) or 1),
            tech_stack=data.get("tech_stack", ""),
            infrastructure_type=data.get("infrastructure_type", "Cloud"),
            status=data.get("status", "In Progress"),
            cpu_utilization=float(data.get("cpu_utilization", 40) or 0),
            memory_utilization=float(data.get("memory_utilization", 40) or 0),
            storage_utilization=float(data.get("storage_utilization", 40) or 0),
            network_utilization=float(data.get("network_utilization", 40) or 0),
            server_availability=float(data.get("server_availability", 99.5) or 0),
            security_incidents=int(data.get("security_incidents", 0) or 0),
            customer_satisfaction=float(data.get("customer_satisfaction", 75) or 0),
            unresolved_issues=int(data.get("unresolved_issues", 0) or 0),
            dependency_delays=int(data.get("dependency_delays", 0) or 0),
        )
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid input: {e}"}), 400

    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict()), 201


@api_bp.route("/projects/<int:project_id>", methods=["GET"])
def api_get_project(project_id):
    project = Project.query.get_or_404(project_id)
    return jsonify(project.to_dict())


# ---------------------------------------------------------------- RISKS
@api_bp.route("/risks", methods=["GET"])
def api_list_risks():
    project_id = request.args.get("project_id", type=int)
    query = Risk.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    risks = query.order_by(Risk.risk_score.desc()).all()
    return jsonify([r.to_dict() for r in risks])


@api_bp.route("/risks", methods=["POST"])
def api_create_risk():
    """Manually add a custom risk to a project."""
    data = request.get_json(force=True, silent=True) or {}
    project_id = data.get("project_id")
    project = Project.query.get(project_id) if project_id else None
    if not project:
        return jsonify({"error": "Valid 'project_id' is required."}), 400
    if not data.get("title") or not data.get("category"):
        return jsonify({"error": "Fields 'title' and 'category' are required."}), 400

    probability = float(data.get("probability", 50) or 0)
    impact = float(data.get("impact", 50) or 0)
    score = round(probability * impact / 100, 1)

    risk = Risk(
        project_id=project.id,
        category=data.get("category"),
        title=data.get("title"),
        description=data.get("description", ""),
        probability=probability,
        impact=impact,
        risk_score=score,
        severity=classify_severity(score),
        root_cause=data.get("root_cause", ""),
        immediate_action=data.get("immediate_action", ""),
        preventive_action=data.get("preventive_action", ""),
        recovery_action=data.get("recovery_action", ""),
        long_term_action=data.get("long_term_action", ""),
        business_impact=data.get("business_impact", ""),
        recommended_owner=data.get("recommended_owner", "Project Manager"),
        difficulty=data.get("difficulty", "Medium"),
        source="manual",
    )
    db.session.add(risk)
    db.session.commit()
    return jsonify(risk.to_dict()), 201


@api_bp.route("/risks/<int:risk_id>/resolve", methods=["POST"])
def api_resolve_risk(risk_id):
    risk = Risk.query.get_or_404(risk_id)
    risk.status = "Resolved"
    db.session.commit()
    return jsonify(risk.to_dict())


# ---------------------------------------------------------------- DASHBOARD
@api_bp.route("/dashboard", methods=["GET"])
def api_dashboard():
    projects = Project.query.all()
    all_risks = Risk.query.all()
    active_risks = [r for r in all_risks if r.status == "Active"]

    if projects:
        healths = [calculate_health_scores(p) for p in projects]
        business_health = round(sum(h["overall_health"] for h in healths) / len(healths), 1)
        avg_budget_health = round(sum(h["financial_health"] for h in healths) / len(healths), 1)
        avg_schedule_health = round(sum(h["schedule_health"] for h in healths) / len(healths), 1)
        avg_security_health = round(sum(h["security_health"] for h in healths) / len(healths), 1)
        avg_infra_health = round(sum(h["technical_health"] for h in healths) / len(healths), 1)
        project_health = round(sum(h["overall_health"] for h in healths) / len(healths), 1)
    else:
        business_health = project_health = avg_budget_health = 0
        avg_schedule_health = avg_security_health = avg_infra_health = 0

    severity_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
    category_counts = {}
    for r in active_risks:
        severity_counts[r.severity] = severity_counts.get(r.severity, 0) + 1
        category_counts[r.category] = category_counts.get(r.category, 0) + 1

    resolved_count = len([r for r in all_risks if r.status == "Resolved"])
    predicted_count = len([r for r in all_risks if r.predicted])
    plans_count = RecoveryPlan.query.count()

    # Risk trend: aggregate RiskHistory across all projects by date
    history = RiskHistory.query.order_by(RiskHistory.recorded_at.asc()).all()
    trend_map = {}
    for h in history:
        key = h.recorded_at.strftime("%Y-%m-%d")
        trend_map.setdefault(key, []).append(h.risk_score)
    risk_trend = [{"date": k, "avg_risk_score": round(sum(v) / len(v), 1)} for k, v in sorted(trend_map.items())]

    all_warnings = []
    for p in projects:
        for w in generate_warnings(p):
            all_warnings.append({**w, "project": p.name, "project_id": p.id})

    return jsonify({
        "business_health": business_health,
        "project_health": project_health,
        "total_projects": len(projects),
        "active_risks": len(active_risks),
        "critical_risks": severity_counts["CRITICAL"],
        "high_risks": severity_counts["HIGH"],
        "resolved_risks": resolved_count,
        "recovery_plans": plans_count,
        "predicted_risks": predicted_count,
        "budget_health": avg_budget_health,
        "schedule_health": avg_schedule_health,
        "security_health": avg_security_health,
        "infrastructure_health": avg_infra_health,
        "severity_distribution": severity_counts,
        "category_distribution": category_counts,
        "risk_trend": risk_trend,
        "warnings": all_warnings,
        "projects_summary": [
            {"id": p.id, "name": p.name, "health": h["overall_health"], "status": p.status}
            for p, h in zip(projects, healths)
        ] if projects else [],
    })


# ---------------------------------------------------------------- ANALYSIS
@api_bp.route("/analyze-risk", methods=["POST"])
def api_analyze_risk():
    data = request.get_json(force=True, silent=True) or {}
    project_id = data.get("project_id")
    project = Project.query.get(project_id) if project_id else None
    if not project:
        return jsonify({"error": "Valid 'project_id' is required."}), 400

    Risk.query.filter_by(project_id=project.id, source="rule-engine", status="Active").update(
        {"status": "Resolved"}
    )
    new_risks = analyze_project(project)
    for r in new_risks:
        db.session.add(r)
    db.session.commit()

    health = calculate_health_scores(project)
    db.session.add(RiskHistory(project_id=project.id, risk_score=health["overall_risk_score"],
                                health_score=health["overall_health"]))
    db.session.commit()

    return jsonify({
        "project": project.to_dict(),
        "health": health,
        "risks": [r.to_dict() for r in new_risks],
        "warnings": generate_warnings(project),
    })


@api_bp.route("/predict-risk", methods=["POST"])
def api_predict_risk():
    data = request.get_json(force=True, silent=True) or {}
    project_id = data.get("project_id")
    project = Project.query.get(project_id) if project_id else None
    if not project:
        return jsonify({"error": "Valid 'project_id' is required."}), 400

    prediction = predict_project_risk(project)
    status = get_model_status()
    return jsonify({"prediction": prediction, "model_status": status})


# ---------------------------------------------------------------- RECOVERY
@api_bp.route("/recovery-plan", methods=["POST"])
def api_recovery_plan():
    data = request.get_json(force=True, silent=True) or {}
    project_id = data.get("project_id")
    project = Project.query.get(project_id) if project_id else None
    if not project:
        return jsonify({"error": "Valid 'project_id' is required."}), 400

    risks = Risk.query.filter_by(project_id=project.id).all()
    content = generate_recovery_plan(project, risks)

    plan = RecoveryPlan(project_id=project.id, title=f"Recovery Plan – {project.name}")
    plan.content = content
    db.session.add(plan)
    db.session.commit()

    return jsonify(plan.to_dict()), 201


# ---------------------------------------------------------------- WHAT-IF
@api_bp.route("/what-if", methods=["POST"])
def api_what_if():
    """
    Body: { "project_id": int, "changes": { "budget_pct": -20, "team_size_delta": -2,
            "progress_delta": 5, "customer_satisfaction_delta": -10,
            "security_incidents_delta": 1, "monthly_cost_pct": 10,
            "infra_utilization_delta": 15 } }
    Returns BEFORE vs AFTER health/risk comparison without persisting anything.
    """
    data = request.get_json(force=True, silent=True) or {}
    project_id = data.get("project_id")
    project = Project.query.get(project_id) if project_id else None
    if not project:
        return jsonify({"error": "Valid 'project_id' is required."}), 400

    changes = data.get("changes", {}) or {}

    before_health = calculate_health_scores(project)
    before_risks = analyze_project(project)

    # Build a lightweight in-memory clone (not persisted) to simulate changes
    class SimProject:
        pass

    sim = SimProject()
    for attr in ["budget", "current_spending", "progress", "expected_progress", "team_size",
                 "cpu_utilization", "memory_utilization", "storage_utilization", "network_utilization",
                 "server_availability", "security_incidents", "customer_satisfaction",
                 "unresolved_issues", "dependency_delays"]:
        setattr(sim, attr, getattr(project, attr))

    if "budget_pct" in changes:
        sim.budget = max(1, project.budget * (1 + float(changes["budget_pct"]) / 100))
    if "monthly_cost_pct" in changes:
        sim.current_spending = max(0, project.current_spending * (1 + float(changes["monthly_cost_pct"]) / 100))
    if "team_size_delta" in changes:
        sim.team_size = max(1, project.team_size + int(changes["team_size_delta"]))
    if "progress_delta" in changes:
        sim.progress = max(0, min(100, project.progress + float(changes["progress_delta"])))
    if "customer_satisfaction_delta" in changes:
        sim.customer_satisfaction = max(0, min(100, project.customer_satisfaction + float(changes["customer_satisfaction_delta"])))
    if "security_incidents_delta" in changes:
        sim.security_incidents = max(0, project.security_incidents + int(changes["security_incidents_delta"]))
    if "infra_utilization_delta" in changes:
        d = float(changes["infra_utilization_delta"])
        sim.cpu_utilization = max(0, min(100, project.cpu_utilization + d))
        sim.memory_utilization = max(0, min(100, project.memory_utilization + d))
        sim.storage_utilization = max(0, min(100, project.storage_utilization + d))
        sim.network_utilization = max(0, min(100, project.network_utilization + d))

    sim.budget_utilization = round((sim.current_spending / sim.budget) * 100, 1) if sim.budget else 0
    sim.schedule_gap = round(sim.expected_progress - sim.progress, 1)

    after_health = calculate_health_scores(sim)
    after_risks = analyze_project_like(sim, project.id)

    explanation = []
    if after_health["overall_health"] < before_health["overall_health"]:
        explanation.append(
            f"Overall health would drop from {before_health['overall_health']} to "
            f"{after_health['overall_health']} due to the simulated changes."
        )
    elif after_health["overall_health"] > before_health["overall_health"]:
        explanation.append(
            f"Overall health would improve from {before_health['overall_health']} to "
            f"{after_health['overall_health']}."
        )
    else:
        explanation.append("Overall health would remain roughly unchanged.")

    if len(after_risks) > len(before_risks):
        explanation.append(f"{len(after_risks) - len(before_risks)} new risk(s) would likely emerge.")
    elif len(after_risks) < len(before_risks):
        explanation.append(f"{len(before_risks) - len(after_risks)} fewer risk(s) would be active.")

    return jsonify({
        "before": {"health": before_health, "risk_count": len(before_risks),
                    "risks": [r.to_dict() for r in before_risks]},
        "after": {"health": after_health, "risk_count": len(after_risks),
                   "risks": [r.to_dict() for r in after_risks]},
        "explanation": " ".join(explanation),
    })


def analyze_project_like(sim, project_id):
    """Run the rule-based risk engine against a simulated (non-persisted) project-like object."""
    sim.id = project_id
    return analyze_project(sim)


# ---------------------------------------------------------------- AI ASSISTANT
@api_bp.route("/ai-assistant", methods=["POST"])
def api_ai_assistant():
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    project_id = data.get("project_id")

    if not question:
        return jsonify({"error": "Field 'question' is required."}), 400

    project = Project.query.get(project_id) if project_id else Project.query.first()
    if not project:
        return jsonify({"answer": "No projects exist yet. Create a project first so I can analyze it.",
                         "mode": "local"}), 200

    risks = Risk.query.filter_by(project_id=project.id).all()
    answer, mode = answer_question(question, project, risks)
    return jsonify({"answer": answer, "mode": mode, "project": project.name})
