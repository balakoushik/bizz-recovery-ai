"""
Analytics Engine: business/project health scoring and early-warning detection.
"""


def _clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def calculate_health_scores(project):
    """Compute component health scores (0-100, higher = healthier) and an
    overall weighted health score, plus the overall risk score (0-100,
    higher = riskier) derived from the same signals."""

    # Financial health: penalize high budget utilization relative to progress
    over_spend = max(0, project.budget_utilization - project.progress)
    financial_health = _clamp(100 - project.budget_utilization * 0.4 - over_spend * 1.2)

    # Schedule health: penalize being behind schedule
    schedule_health = _clamp(100 - max(0, project.schedule_gap) * 2.2)

    # Technical/infrastructure health
    max_infra = max(project.cpu_utilization, project.memory_utilization,
                     project.storage_utilization, project.network_utilization)
    technical_health = _clamp(100 - max(0, max_infra - 50) * 1.4)

    # Security health
    security_health = _clamp(100 - project.security_incidents * 18)

    # Resource health (team adequacy heuristic, mirrors risk_engine)
    expected_team = max(2, round(project.budget / 120000)) if project.budget else project.team_size
    shortfall = max(0, expected_team - project.team_size)
    resource_health = _clamp(100 - shortfall * 12)

    # Customer health
    customer_health = _clamp(project.customer_satisfaction)

    # Operational health (issue backlog + dependency delays)
    operational_health = _clamp(100 - project.unresolved_issues * 2.2 - project.dependency_delays * 8)

    components = {
        "financial_health": round(financial_health, 1),
        "schedule_health": round(schedule_health, 1),
        "technical_health": round(technical_health, 1),
        "security_health": round(security_health, 1),
        "resource_health": round(resource_health, 1),
        "customer_health": round(customer_health, 1),
        "operational_health": round(operational_health, 1),
    }

    weights = {
        "financial_health": 0.20,
        "schedule_health": 0.18,
        "technical_health": 0.15,
        "security_health": 0.15,
        "resource_health": 0.12,
        "customer_health": 0.10,
        "operational_health": 0.10,
    }

    overall_health = round(sum(components[k] * weights[k] for k in weights), 1)
    overall_risk_score = round(100 - overall_health, 1)

    return {
        **components,
        "overall_health": overall_health,
        "overall_risk_score": overall_risk_score,
    }


def generate_warnings(project):
    """Detect dangerous trends and produce human-readable early warnings."""
    warnings = []

    if project.budget_utilization >= 85:
        warnings.append({
            "severity": "HIGH" if project.budget_utilization < 100 else "CRITICAL",
            "message": (
                f"Budget consumption has reached {project.budget_utilization}% of total budget "
                f"while progress is at {project.progress}%. Potential budget overrun detected."
            ),
        })

    if project.schedule_gap >= 8:
        warnings.append({
            "severity": "HIGH" if project.schedule_gap < 20 else "CRITICAL",
            "message": f"Project progress is {project.schedule_gap}% behind expected schedule.",
        })

    max_infra = max(project.cpu_utilization, project.memory_utilization,
                     project.storage_utilization, project.network_utilization)
    if max_infra >= 85:
        warnings.append({
            "severity": "HIGH",
            "message": f"Infrastructure utilization has reached {max_infra}%. Capacity risk is rising.",
        })

    if project.security_incidents >= 2:
        warnings.append({
            "severity": "CRITICAL",
            "message": f"{project.security_incidents} security incidents recorded — immediate review recommended.",
        })

    if project.customer_satisfaction < 60:
        warnings.append({
            "severity": "MEDIUM" if project.customer_satisfaction >= 45 else "HIGH",
            "message": f"Customer satisfaction has dropped to {project.customer_satisfaction}/100.",
        })

    if project.dependency_delays >= 2:
        warnings.append({
            "severity": "MEDIUM",
            "message": f"{project.dependency_delays} external dependencies are delayed, threatening the critical path.",
        })

    if project.server_availability < 99.0:
        warnings.append({
            "severity": "HIGH",
            "message": f"Server availability has fallen to {project.server_availability}%, below the 99% target.",
        })

    return warnings
