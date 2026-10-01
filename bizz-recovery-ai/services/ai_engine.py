"""
AI Business Assistant Engine.

LOCAL INTELLIGENCE MODE (default, no API key required):
  Rule-based natural-language reasoning grounded entirely in the
  project's real stored data (risks, health scores, warnings).

OPTIONAL EXTERNAL LLM MODE:
  If ANTHROPIC_API_KEY is configured, the same grounded context is
  sent to Claude to produce a richer natural-language answer. If the
  call fails for any reason, it silently falls back to local mode.
"""
import re
import requests
from flask import current_app
from services.analytics_engine import calculate_health_scores, generate_warnings


def _build_context(project, risks):
    health = calculate_health_scores(project)
    warnings = generate_warnings(project)
    active_risks = sorted([r for r in risks if r.status == "Active"],
                           key=lambda r: r.risk_score, reverse=True)
    return health, warnings, active_risks


def _local_answer(question, project, risks):
    """Rule-based intent matching over the user's real project data."""
    q = question.lower().strip()
    health, warnings, active_risks = _build_context(project, risks)

    def top_risk_text():
        if not active_risks:
            return "no active risks are currently detected for this project."
        r = active_risks[0]
        return (f"your biggest risk is **{r.title}** ({r.category}), severity {r.severity}, "
                f"with a risk score of {r.risk_score}/100. Root cause: {r.root_cause}")

    if re.search(r"biggest risk|top risk|main risk|highest risk", q):
        return f"Based on current data, {top_risk_text()}"

    if re.search(r"why.*(at risk|risky)|why.*health.*low|why.*score.*low", q):
        weakest = min(
            ["financial_health", "schedule_health", "technical_health", "security_health",
             "resource_health", "customer_health", "operational_health"],
            key=lambda k: health[k],
        )
        label = weakest.replace("_", " ").title()
        return (f"Your overall health score is {health['overall_health']}/100. The weakest area is "
                f"**{label}** at {health[weakest]}/100, which is dragging the overall score down. "
                f"{top_risk_text().capitalize()}")

    if re.search(r"financial risk|reduce.*financial|budget risk", q):
        fin_risks = [r for r in active_risks if r.category == "FINANCIAL"]
        if fin_risks:
            r = fin_risks[0]
            return (f"To reduce financial risk: {r.immediate_action} Also consider: {r.preventive_action} "
                    f"Current budget utilization is {project.budget_utilization}% vs {project.progress}% progress.")
        return (f"No active financial risk is currently detected. Budget utilization is "
                f"{project.budget_utilization}% against {project.progress}% progress, which looks healthy.")

    if re.search(r"team size decrease|lose.*team|fewer people|reduce team", q):
        return (f"Reducing team size below the current {project.team_size} would likely worsen schedule "
                f"and resource risk, since the project's expected schedule gap and open issue backlog "
                f"({project.unresolved_issues} unresolved) would take longer to close. Use the What-If "
                f"Simulation page to model this precisely.")

    if re.search(r"recovery plan|how do i recover|fix.*project", q):
        if not active_risks:
            return "No active risks are detected, so a full recovery plan isn't needed right now — keep monitoring."
        return (f"I'd recommend generating a full Recovery Plan from the Recovery Plans page — it will "
                f"sequence immediate, short-term, and long-term actions for your {len(active_risks)} "
                f"active risk(s), starting with {active_risks[0].title}.")

    if re.search(r"prioriti[sz]e|what should i (do|focus)", q):
        top3 = active_risks[:3]
        if not top3:
            return "No active risks are detected — focus on maintaining current health scores."
        lines = [f"{i+1}. {r.title} ({r.severity}, score {r.risk_score})" for i, r in enumerate(top3)]
        return "Prioritize in this order:\n" + "\n".join(lines)

    if re.search(r"warning|alert", q):
        if not warnings:
            return "No active early warnings for this project right now."
        return "Current warnings:\n" + "\n".join(f"- [{w['severity']}] {w['message']}" for w in warnings)

    if re.search(r"security", q):
        sec_risks = [r for r in active_risks if r.category == "SECURITY"]
        if sec_risks:
            r = sec_risks[0]
            return f"Security concern detected: {r.description} Immediate action: {r.immediate_action}"
        return f"No active security risk detected. Security health score is {health['security_health']}/100."

    if re.search(r"health score|overall health|how (is|are) (my|the) project", q):
        return (f"Overall health score is {health['overall_health']}/100 "
                f"(Financial {health['financial_health']}, Schedule {health['schedule_health']}, "
                f"Technical {health['technical_health']}, Security {health['security_health']}, "
                f"Resource {health['resource_health']}, Customer {health['customer_health']}, "
                f"Operational {health['operational_health']}).")

    # Default fallback: general summary
    return (f"Here's a snapshot of **{project.name}**: overall health {health['overall_health']}/100, "
            f"{len(active_risks)} active risk(s). {top_risk_text().capitalize()} "
            f"Ask me things like \"What's my biggest risk?\", \"How can I reduce my financial risk?\", "
            f"or \"Give me a recovery plan.\"")


def _external_llm_answer(question, project, risks, api_key):
    health, warnings, active_risks = _build_context(project, risks)
    context_summary = {
        "project": project.to_dict(),
        "health_scores": health,
        "warnings": warnings,
        "top_risks": [r.to_dict() for r in active_risks[:6]],
    }

    system_prompt = (
        "You are the AI Business Assistant inside Bizz Recovery AI, a business/project risk "
        "management platform. Answer the user's question using ONLY the structured project data "
        "provided below. Be concise, concrete, and reference actual numbers from the data. "
        "If the data doesn't support an answer, say so honestly.\n\n"
        f"PROJECT DATA:\n{context_summary}"
    )

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 500,
                "system": system_prompt,
                "messages": [{"role": "user", "content": question}],
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        text_blocks = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
        if text_blocks:
            return "\n".join(text_blocks), "external-llm"
    except Exception as e:
        print(f"[ai_engine] External LLM call failed, falling back to local mode. Reason: {e}")

    return _local_answer(question, project, risks), "local-fallback"


def answer_question(question, project, risks):
    """Main entry point. Returns (answer_text, mode)."""
    api_key = current_app.config.get("ANTHROPIC_API_KEY", "")
    if api_key:
        return _external_llm_answer(question, project, risks, api_key)
    return _local_answer(question, project, risks), "local"
