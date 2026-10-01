from datetime import datetime
from database.database import db


class Risk(db.Model):
    __tablename__ = "risks"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)

    category = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")

    probability = db.Column(db.Float, default=0)   # 0-100
    impact = db.Column(db.Float, default=0)         # 0-100
    risk_score = db.Column(db.Float, default=0)     # probability * impact / 100
    severity = db.Column(db.String(20), default="LOW")

    expected_loss = db.Column(db.Float, default=0)
    priority = db.Column(db.String(20), default="Low")
    urgency = db.Column(db.String(20), default="Low")

    root_cause = db.Column(db.Text, default="")
    immediate_action = db.Column(db.Text, default="")
    preventive_action = db.Column(db.Text, default="")
    recovery_action = db.Column(db.Text, default="")
    long_term_action = db.Column(db.Text, default="")
    business_impact = db.Column(db.Text, default="")
    recommended_owner = db.Column(db.String(100), default="Project Manager")
    difficulty = db.Column(db.String(20), default="Medium")

    source = db.Column(db.String(20), default="rule-engine")  # rule-engine | ml-model
    status = db.Column(db.String(20), default="Active")        # Active | Resolved
    predicted = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "probability": self.probability,
            "impact": self.impact,
            "risk_score": self.risk_score,
            "severity": self.severity,
            "expected_loss": self.expected_loss,
            "priority": self.priority,
            "urgency": self.urgency,
            "root_cause": self.root_cause,
            "immediate_action": self.immediate_action,
            "preventive_action": self.preventive_action,
            "recovery_action": self.recovery_action,
            "long_term_action": self.long_term_action,
            "business_impact": self.business_impact,
            "recommended_owner": self.recommended_owner,
            "difficulty": self.difficulty,
            "source": self.source,
            "status": self.status,
            "predicted": self.predicted,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M") if self.created_at else None,
        }


class RiskHistory(db.Model):
    __tablename__ = "risk_history"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    risk_score = db.Column(db.Float, default=0)
    health_score = db.Column(db.Float, default=0)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "risk_score": self.risk_score,
            "health_score": self.health_score,
            "recorded_at": self.recorded_at.strftime("%Y-%m-%d %H:%M"),
        }


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default="MEDIUM")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "message": self.message,
            "severity": self.severity,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }
