"""
AI Recovery Plan Generator — assembles a full structured recovery plan
from a project's current risks and health data.
"""
from datetime import datetime, timedelta
from services.analytics_engine import calculate_health_scores


def _difficulty_to_days(difficulty):
    return {"Low": 7, "Medium": 21, "High": 45}.get(difficulty, 21)


def generate_recovery_plan(project, risks):
    health = calculate_health_scores(project)
    active_risks = [r for r in risks if r.status == "Active"]
    critical = [r for r in active_risks if r.severity == "CRITICAL"]
    high = [r for r in active_risks if r.severity == "HIGH"]

    sorted_risks = sorted(active_risks, key=lambda r: r.risk_score, reverse=True)
    top_risks = sorted_risks[:5]

    max_days = max([_difficulty_to_days(r.difficulty) for r in active_risks], default=14)
    timeline_end = datetime.utcnow() + timedelta(days=max_days)

    estimated_cost = round(sum(r.expected_loss for r in active_risks) * 0.35, 2)

    exec_summary = (
        f"{project.name} currently has an overall health score of {health['overall_health']}/100 "
        f"with {len(active_risks)} active risk(s), including {len(critical)} critical and "
        f"{len(high)} high-severity risk(s). This recovery plan prioritizes the highest-impact "
        f"risks first and lays out immediate, short-term, and long-term actions to restore project health."
    )

    current_situation = (
        f"Budget utilization is {project.budget_utilization}% against {project.progress}% progress "
        f"(expected {project.expected_progress}%). Team size is {project.team_size}, with "
        f"{project.unresolved_issues} unresolved issues and {project.security_incidents} security "
        f"incident(s) on record. Customer satisfaction stands at {project.customer_satisfaction}/100."
    )

    root_causes = list({r.root_cause for r in top_risks if r.root_cause})
    immediate_actions = [f"[{r.severity}] {r.title}: {r.immediate_action}" for r in top_risks]
    short_term = [f"[{r.severity}] {r.title}: {r.recovery_action}" for r in top_risks]
    long_term = list({r.long_term_action for r in top_risks if r.long_term_action})
    required_resources = list({r.recommended_owner for r in active_risks})

    success_metrics = [
        f"Overall health score improves from {health['overall_health']}/100 to 80+/100",
        "Zero CRITICAL-severity active risks",
        f"Budget utilization brought back in line with progress (target gap < 10%)",
        "Schedule gap reduced to under 5%",
    ]

    monitoring_plan = (
        "Re-run risk analysis weekly, track health score trend on the dashboard, "
        "and review this recovery plan bi-weekly until all CRITICAL and HIGH risks are resolved."
    )

    content = {
        "executive_summary": exec_summary,
        "current_situation": current_situation,
        "detected_risks": [r.to_dict() for r in sorted_risks],
        "risk_severity_breakdown": {
            "CRITICAL": len(critical),
            "HIGH": len(high),
            "MEDIUM": len([r for r in active_risks if r.severity == "MEDIUM"]),
            "LOW": len([r for r in active_risks if r.severity == "LOW"]),
        },
        "root_causes": root_causes,
        "immediate_actions": immediate_actions,
        "short_term_recovery": short_term,
        "long_term_recovery": long_term,
        "required_resources": required_resources,
        "estimated_cost": estimated_cost,
        "responsible_team": required_resources[0] if required_resources else "Project Manager",
        "recovery_timeline": {
            "start": datetime.utcnow().strftime("%Y-%m-%d"),
            "target_completion": timeline_end.strftime("%Y-%m-%d"),
            "duration_days": max_days,
        },
        "success_metrics": success_metrics,
        "monitoring_plan": monitoring_plan,
        "health_snapshot": health,
    }

    return content
