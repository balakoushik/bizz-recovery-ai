"""
Machine Learning Risk Prediction Module.

Trains a RandomForestClassifier on synthetically generated (but
realistically distributed) project data to predict overall project
risk/failure probability and severity band. Because real historical
data is unavailable, this is honestly labeled as a HEURISTIC MODEL
and its confidence is reported transparently rather than overstated.

If scikit-learn is unavailable or training fails for any reason, the
module gracefully falls back to a simple weighted-average rule so the
rest of the application keeps working.
"""
import numpy as np

FEATURE_NAMES = [
    "budget_utilization", "schedule_gap", "team_size", "progress",
    "unresolved_issues", "security_incidents", "customer_satisfaction",
    "max_infra_utilization", "dependency_delays",
]

_model = None
_model_ready = False
_train_accuracy = None

SEVERITY_LABELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def _generate_synthetic_dataset(n=1500, seed=42):
    """Generate a synthetic-but-plausible training set from feature
    distributions and a transparent rule-based label function, so the
    classifier learns interactions similar to the rule engine while
    still being a genuine trained ML model."""
    rng = np.random.default_rng(seed)

    budget_utilization = rng.uniform(10, 130, n)
    schedule_gap = rng.uniform(-15, 40, n)
    team_size = rng.integers(1, 25, n)
    progress = rng.uniform(0, 100, n)
    unresolved_issues = rng.integers(0, 40, n)
    security_incidents = rng.integers(0, 6, n)
    customer_satisfaction = rng.uniform(20, 100, n)
    max_infra_utilization = rng.uniform(10, 100, n)
    dependency_delays = rng.integers(0, 5, n)

    X = np.column_stack([
        budget_utilization, schedule_gap, team_size, progress,
        unresolved_issues, security_incidents, customer_satisfaction,
        max_infra_utilization, dependency_delays,
    ])

    # Composite synthetic risk score used only to LABEL training data
    score = (
        (budget_utilization / 130) * 22
        + (np.clip(schedule_gap, 0, None) / 40) * 20
        + (unresolved_issues / 40) * 12
        + (security_incidents / 6) * 15
        + ((100 - customer_satisfaction) / 100) * 13
        + (max_infra_utilization / 100) * 12
        + (dependency_delays / 5) * 6
    )
    score += rng.normal(0, 6, n)  # noise so it's not a trivial linear rule
    score = np.clip(score, 0, 100)

    labels = np.digitize(score, bins=[25, 50, 75])  # 0=LOW..3=CRITICAL
    return X, labels


def _train_model():
    global _model, _model_ready, _train_accuracy
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score

        X, y = _generate_synthetic_dataset()
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        clf = RandomForestClassifier(
            n_estimators=150, max_depth=8, random_state=42, n_jobs=-1
        )
        clf.fit(X_train, y_train)
        preds = clf.predict(X_test)
        _train_accuracy = round(float(accuracy_score(y_test, preds)) * 100, 1)
        _model = clf
        _model_ready = True
    except Exception as e:  # graceful fallback - never crash the app
        _model = None
        _model_ready = False
        _train_accuracy = None
        print(f"[prediction_engine] ML model unavailable, using fallback. Reason: {e}")


def get_model_status():
    if not _model_ready and _model is None:
        _train_model()
    return {
        "ml_available": _model_ready,
        "model": "RandomForestClassifier (scikit-learn)" if _model_ready else "Rule-based fallback",
        "trained_on": "1,500 synthetically generated project samples" if _model_ready else None,
        "holdout_accuracy_pct": _train_accuracy,
        "disclaimer": (
            "This model is trained on synthetically generated data patterned after "
            "common project-risk indicators, not on your organization's historical "
            "outcomes. Treat predictions as a decision-support signal, not ground truth."
        ),
    }


def _extract_features(project):
    max_infra = max(
        project.cpu_utilization, project.memory_utilization,
        project.storage_utilization, project.network_utilization,
    )
    return np.array([[
        project.budget_utilization,
        project.schedule_gap,
        project.team_size,
        project.progress,
        project.unresolved_issues,
        project.security_incidents,
        project.customer_satisfaction,
        max_infra,
        project.dependency_delays,
    ]])


def predict_project_risk(project):
    """Return predicted failure/risk probability, severity band, and
    confidence for a given project, using the ML model if available."""
    if not _model_ready and _model is None:
        _train_model()

    features = _extract_features(project)

    if _model_ready and _model is not None:
        probs = _model.predict_proba(features)[0]
        # probability of risk = P(HIGH) + P(CRITICAL)
        classes = list(_model.classes_)
        risk_prob = 0.0
        for cls_idx, cls in enumerate(classes):
            if cls >= 2:  # HIGH or CRITICAL
                risk_prob += probs[cls_idx]
        predicted_class = int(np.argmax(probs))
        confidence = round(float(np.max(probs)) * 100, 1)
        return {
            "method": "ml-model",
            "predicted_severity": SEVERITY_LABELS[predicted_class],
            "risk_probability_pct": round(risk_prob * 100, 1),
            "confidence_pct": confidence,
            "class_probabilities": {
                SEVERITY_LABELS[i]: round(float(probs[list(classes).index(i)]) * 100, 1)
                for i in range(len(SEVERITY_LABELS)) if i in classes
            },
        }

    # ---- Fallback: transparent weighted heuristic ----
    from services.risk_engine import classify_severity
    max_infra = max(
        project.cpu_utilization, project.memory_utilization,
        project.storage_utilization, project.network_utilization,
    )
    score = (
        min(project.budget_utilization, 130) / 130 * 22
        + max(project.schedule_gap, 0) / 40 * 20
        + min(project.unresolved_issues, 40) / 40 * 12
        + min(project.security_incidents, 6) / 6 * 15
        + (100 - project.customer_satisfaction) / 100 * 13
        + max_infra / 100 * 12
        + min(project.dependency_delays, 5) / 5 * 6
    )
    score = max(0, min(100, score))
    return {
        "method": "rule-based-fallback",
        "predicted_severity": classify_severity(score),
        "risk_probability_pct": round(score, 1),
        "confidence_pct": 55.0,  # honestly modest, since it's a heuristic
        "class_probabilities": None,
    }


# Pre-warm the model at import time (fails silently to fallback if needed)
_train_model()
