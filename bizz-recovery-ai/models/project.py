from datetime import datetime
from database.database import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    industry = db.Column(db.String(80), default="Software")

    budget = db.Column(db.Float, default=0)
    current_spending = db.Column(db.Float, default=0)

    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    expected_end_date = db.Column(db.DateTime, default=datetime.utcnow)

    progress = db.Column(db.Float, default=0)            # actual % complete
    expected_progress = db.Column(db.Float, default=0)    # % complete expected by now

    team_size = db.Column(db.Integer, default=1)
    tech_stack = db.Column(db.String(255), default="")
    infrastructure_type = db.Column(db.String(120), default="Cloud")
    status = db.Column(db.String(40), default="In Progress")

    # Infrastructure / operational signals
    cpu_utilization = db.Column(db.Float, default=40)
    memory_utilization = db.Column(db.Float, default=40)
    storage_utilization = db.Column(db.Float, default=40)
    network_utilization = db.Column(db.Float, default=40)
    server_availability = db.Column(db.Float, default=99.5)

    # Risk signal inputs
    security_incidents = db.Column(db.Integer, default=0)
    customer_satisfaction = db.Column(db.Float, default=75)
    unresolved_issues = db.Column(db.Integer, default=0)
    dependency_delays = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    risks = db.relationship("Risk", backref="project", lazy=True, cascade="all, delete-orphan")
    recovery_plans = db.relationship("RecoveryPlan", backref="project", lazy=True, cascade="all, delete-orphan")
    history = db.relationship("RiskHistory", backref="project", lazy=True, cascade="all, delete-orphan")
    alerts = db.relationship("Alert", backref="project", lazy=True, cascade="all, delete-orphan")

    # ---- Derived convenience properties ----
    @property
    def budget_utilization(self):
        if not self.budget:
            return 0
        return round((self.current_spending / self.budget) * 100, 1)

    @property
    def schedule_gap(self):
        """Positive value = behind schedule."""
        return round(self.expected_progress - self.progress, 1)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "industry": self.industry,
            "budget": self.budget,
            "current_spending": self.current_spending,
            "budget_utilization": self.budget_utilization,
            "start_date": self.start_date.strftime("%Y-%m-%d") if self.start_date else None,
            "expected_end_date": self.expected_end_date.strftime("%Y-%m-%d") if self.expected_end_date else None,
            "progress": self.progress,
            "expected_progress": self.expected_progress,
            "schedule_gap": self.schedule_gap,
            "team_size": self.team_size,
            "tech_stack": self.tech_stack,
            "infrastructure_type": self.infrastructure_type,
            "status": self.status,
            "cpu_utilization": self.cpu_utilization,
            "memory_utilization": self.memory_utilization,
            "storage_utilization": self.storage_utilization,
            "network_utilization": self.network_utilization,
            "server_availability": self.server_availability,
            "security_incidents": self.security_incidents,
            "customer_satisfaction": self.customer_satisfaction,
            "unresolved_issues": self.unresolved_issues,
            "dependency_delays": self.dependency_delays,
            "created_at": self.created_at.strftime("%Y-%m-%d") if self.created_at else None,
        }
