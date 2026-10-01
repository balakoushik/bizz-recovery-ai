"""
Rule-based Risk Identification & Scoring Engine.

Given a Project record, inspects its real fields (budget, schedule,
team size, infrastructure utilization, security incidents, customer
satisfaction, dependencies, etc.) and produces a list of unsaved
Risk objects ready to be committed to the database.

Risk Score = Probability * Impact / 100
Severity thresholds: LOW 0-24, MEDIUM 25-49, HIGH 50-74, CRITICAL 75-100
"""
from models.risk import Risk


def classify_severity(score):
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    return "LOW"


def _priority_urgency(score):
    severity = classify_severity(score)
    mapping = {
        "CRITICAL": ("Immediate", "Very High"),
        "HIGH": ("High", "High"),
        "MEDIUM": ("Medium", "Moderate"),
        "LOW": ("Low", "Low"),
    }
    return mapping[severity]


def _make_risk(project, category, title, description, probability, impact,
               root_cause, immediate, preventive, recovery, long_term,
               business_impact, owner, difficulty, source="rule-engine", predicted=False):
    probability = max(0, min(100, round(probability, 1)))
    impact = max(0, min(100, round(impact, 1)))
    score = round(probability * impact / 100, 1)
    severity = classify_severity(score)
    priority, urgency = _priority_urgency(score)
    expected_loss = round((score / 100) * project.budget * 0.15, 2) if project.budget else 0

    return Risk(
        project_id=project.id,
        category=category,
        title=title,
        description=description,
        probability=probability,
        impact=impact,
        risk_score=score,
        severity=severity,
        expected_loss=expected_loss,
        priority=priority,
        urgency=urgency,
        root_cause=root_cause,
        immediate_action=immediate,
        preventive_action=preventive,
        recovery_action=recovery,
        long_term_action=long_term,
        business_impact=business_impact,
        recommended_owner=owner,
        difficulty=difficulty,
        source=source,
        predicted=predicted,
    )


def analyze_project(project):
    """Return a list of unsaved Risk objects detected for this project."""
    risks = []

    # ---- 1. FINANCIAL / Budget Overrun ----
    util = project.budget_utilization
    progress = project.progress or 0.01
    spend_vs_progress = util - progress  # spending outpacing delivered progress
    if util >= 70 or spend_vs_progress >= 15:
        probability = min(95, 40 + util * 0.5)
        impact = min(95, 50 + max(0, spend_vs_progress))
        risks.append(_make_risk(
            project, "FINANCIAL", "Budget Overrun Risk",
            f"Budget utilization is {util}% while project progress is only {project.progress}%.",
            probability, impact,
            root_cause="Project spending is increasing faster than the pace of delivered work.",
            immediate="Freeze non-critical spending and audit recent expenditure.",
            preventive="Introduce weekly budget monitoring with variance alerts.",
            recovery="Review resource allocation and postpone low-priority features.",
            long_term="Adopt rolling budget forecasts tied to milestone-based delivery.",
            business_impact="Cost overrun may erode project ROI and delay other funded initiatives.",
            owner="Finance / Project Manager",
            difficulty="Medium",
        ))

    # ---- 2. SCHEDULE / Delay ----
    gap = project.schedule_gap
    if gap >= 8:
        probability = min(95, 45 + gap * 1.5)
        impact = min(95, 40 + gap * 1.2)
        risks.append(_make_risk(
            project, "SCHEDULE", "Schedule Delay Risk",
            f"Project progress is {gap}% behind the expected schedule position.",
            probability, impact,
            root_cause="Actual delivery velocity is lower than planned velocity.",
            immediate="Re-baseline the sprint/milestone plan and identify blocked tasks.",
            preventive="Adopt earlier milestone checkpoints and buffer time in estimates.",
            recovery="Reprioritize backlog, consider scope reduction or additional short-term resources.",
            long_term="Improve estimation accuracy using historical velocity data.",
            business_impact="Late delivery risks contractual penalties and stakeholder confidence.",
            owner="Project Manager",
            difficulty="Medium",
        ))

    # ---- 3. RESOURCE / Team Size ----
    # Heuristic: larger, more complex projects (higher budget) need proportionally more people.
    expected_team = max(2, round(project.budget / 120000)) if project.budget else project.team_size
    if project.team_size < expected_team * 0.7:
        probability = min(90, 35 + (expected_team - project.team_size) * 8)
        impact = min(90, 30 + (expected_team - project.team_size) * 6)
        risks.append(_make_risk(
            project, "RESOURCE", "Resource Shortage Risk",
            f"Team size of {project.team_size} appears undersized relative to project scope "
            f"(estimated need ~{expected_team}).",
            probability, impact,
            root_cause="Insufficient staffing relative to workload and project complexity.",
            immediate="Assess current team workload and identify critical skill gaps.",
            preventive="Establish a staffing plan tied to project milestones.",
            recovery="Bring in contractors or reassign staff from lower-priority initiatives.",
            long_term="Build a resource forecasting process into project planning.",
            business_impact="Understaffing increases burnout risk and slows delivery further.",
            owner="Resource Manager / PM",
            difficulty="Medium",
        ))

    # ---- 4. INFRASTRUCTURE / Utilization ----
    max_util = max(project.cpu_utilization, project.memory_utilization, project.storage_utilization,
                    project.network_utilization)
    if max_util >= 80:
        probability = min(95, 40 + max_util * 0.55)
        impact = min(95, 45 + max_util * 0.45)
        which = []
        if project.cpu_utilization >= 80:
            which.append("CPU")
        if project.memory_utilization >= 80:
            which.append("Memory")
        if project.storage_utilization >= 80:
            which.append("Storage")
        if project.network_utilization >= 80:
            which.append("Network")
        risks.append(_make_risk(
            project, "INFRASTRUCTURE", "Infrastructure Capacity Risk",
            f"High utilization detected: {', '.join(which)} at or above 80%.",
            probability, impact,
            root_cause="Infrastructure capacity is not scaling with current demand.",
            immediate="Enable autoscaling or provision additional capacity immediately.",
            preventive="Set proactive utilization alert thresholds at 70%.",
            recovery="Right-size infrastructure and optimize resource-heavy processes.",
            long_term="Move to elastic, demand-based cloud infrastructure architecture.",
            business_impact="Risk of downtime, degraded performance, and customer impact.",
            owner="Infrastructure / DevOps Team",
            difficulty="Medium",
        ))

    if project.server_availability < 99.0:
        probability = min(95, 100 - project.server_availability * 0.9)
        impact = 80
        risks.append(_make_risk(
            project, "INFRASTRUCTURE", "Service Availability Risk",
            f"Server availability is {project.server_availability}%, below the 99% target.",
            probability, impact,
            root_cause="Frequent outages or unstable infrastructure components.",
            immediate="Investigate recent incidents and root-cause the outages.",
            preventive="Implement redundancy and automated failover.",
            recovery="Deploy monitoring/alerting and a documented incident response plan.",
            long_term="Design for high availability (multi-AZ / multi-region).",
            business_impact="Downtime directly affects revenue and customer trust.",
            owner="Infrastructure / DevOps Team",
            difficulty="High",
        ))

    # ---- 5. SECURITY ----
    if project.security_incidents > 0:
        probability = min(95, 30 + project.security_incidents * 20)
        impact = min(95, 50 + project.security_incidents * 15)
        risks.append(_make_risk(
            project, "SECURITY", "Security Incident Risk",
            f"{project.security_incidents} security incident(s) recorded for this project.",
            probability, impact,
            root_cause="Gaps in access control, patching, or monitoring allowed incidents to occur.",
            immediate="Contain affected systems and rotate exposed credentials.",
            preventive="Enable MFA, enforce least-privilege access, patch known vulnerabilities.",
            recovery="Conduct a full security audit and remediate identified gaps.",
            long_term="Establish continuous security monitoring and periodic penetration testing.",
            business_impact="Security incidents risk data breach, compliance fines, and reputational damage.",
            owner="Security Team",
            difficulty="High",
        ))

    # ---- 6. CUSTOMER / Satisfaction ----
    if project.customer_satisfaction < 65:
        probability = min(90, 100 - project.customer_satisfaction)
        impact = min(90, 90 - project.customer_satisfaction * 0.5)
        risks.append(_make_risk(
            project, "CUSTOMER", "Customer Churn Risk",
            f"Customer satisfaction score is {project.customer_satisfaction}/100, below healthy levels.",
            probability, impact,
            root_cause="Product/service quality or delivery issues are affecting customer experience.",
            immediate="Reach out to key affected customers and gather direct feedback.",
            preventive="Set up continuous satisfaction tracking (NPS/CSAT surveys).",
            recovery="Prioritize fixes for the top customer-reported issues.",
            long_term="Build a customer success program with proactive engagement.",
            business_impact="Low satisfaction increases churn and reduces referral/expansion revenue.",
            owner="Customer Success Team",
            difficulty="Medium",
        ))

    # ---- 7. SUPPLY CHAIN / Dependency Delays ----
    if project.dependency_delays > 0:
        probability = min(90, 35 + project.dependency_delays * 20)
        impact = min(85, 30 + project.dependency_delays * 18)
        risks.append(_make_risk(
            project, "SUPPLY CHAIN", "Dependency / Vendor Delay Risk",
            f"{project.dependency_delays} delayed external dependency/dependencies detected.",
            probability, impact,
            root_cause="Third-party vendors or upstream teams are not delivering on schedule.",
            immediate="Escalate with the vendor/dependency owner and get a revised timeline.",
            preventive="Maintain a dependency tracker with buffer time for external deliverables.",
            recovery="Identify workarounds or alternate vendors for critical path items.",
            long_term="Diversify critical suppliers/dependencies to reduce single points of failure.",
            business_impact="Delays cascade into the overall project timeline and cost.",
            owner="Procurement / Project Manager",
            difficulty="Medium",
        ))

    # ---- 8. OPERATIONAL / Unresolved Issues backlog ----
    if project.unresolved_issues >= 10:
        probability = min(90, 30 + project.unresolved_issues * 2)
        impact = min(85, 25 + project.unresolved_issues * 1.5)
        risks.append(_make_risk(
            project, "OPERATIONAL", "Operational Backlog Risk",
            f"{project.unresolved_issues} unresolved issues are currently open.",
            probability, impact,
            root_cause="Issue triage and resolution throughput is not keeping pace with intake.",
            immediate="Triage the backlog and address blocking/critical issues first.",
            preventive="Set SLAs for issue resolution by severity.",
            recovery="Allocate a dedicated sprint or team to reduce the backlog.",
            long_term="Improve QA and root-cause analysis to reduce issue recurrence.",
            business_impact="Growing backlog increases technical debt and delivery risk.",
            owner="Engineering Lead",
            difficulty="Medium",
        ))

    return risks
