"""
Central SQLAlchemy instance + database bootstrap / sample-data seeding.
"""
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """Create all tables and seed sample data if the DB is empty."""
    with app.app_context():
        # Import models so SQLAlchemy knows about them before create_all()
        from models.project import Project
        from models.risk import Risk, RiskHistory, Alert
        from models.recovery import RecoveryPlan
        from models.user import User

        db.create_all()

        if Project.query.count() == 0:
            _seed_sample_data(db)


def _seed_sample_data(db):
    from models.project import Project
    from models.user import User

    if User.query.count() == 0:
        admin = User(username="admin", email="admin@bizzrecovery.ai")
        admin.set_password("admin123")
        db.session.add(admin)

    today = datetime.utcnow()

    sample_projects = [
        dict(
            name="E-Commerce Platform",
            description="Customer-facing online retail platform with payment integration.",
            industry="E-commerce",
            budget=500000,
            current_spending=410000,
            start_date=today - timedelta(days=150),
            expected_end_date=today + timedelta(days=60),
            progress=62,
            expected_progress=75,
            team_size=6,
            tech_stack="React, Node.js, MongoDB",
            infrastructure_type="Cloud (AWS)",
            status="In Progress",
            cpu_utilization=88,
            memory_utilization=79,
            storage_utilization=71,
            network_utilization=65,
            server_availability=97.2,
            security_incidents=2,
            customer_satisfaction=58,
            unresolved_issues=14,
            dependency_delays=1,
        ),
        dict(
            name="Core Banking Migration",
            description="Migration of legacy core banking system to a modern microservices architecture.",
            industry="Banking",
            budget=2000000,
            current_spending=1250000,
            start_date=today - timedelta(days=220),
            expected_end_date=today + timedelta(days=140),
            progress=48,
            expected_progress=55,
            team_size=14,
            tech_stack="Java, Spring Boot, PostgreSQL, Kafka",
            infrastructure_type="Hybrid Cloud",
            status="In Progress",
            cpu_utilization=62,
            memory_utilization=58,
            storage_utilization=66,
            network_utilization=54,
            server_availability=99.4,
            security_incidents=0,
            customer_satisfaction=74,
            unresolved_issues=6,
            dependency_delays=0,
        ),
        dict(
            name="Healthcare Patient Portal",
            description="Patient scheduling, records, and telehealth portal.",
            industry="Healthcare",
            budget=350000,
            current_spending=340000,
            start_date=today - timedelta(days=300),
            expected_end_date=today - timedelta(days=10),
            progress=91,
            expected_progress=100,
            team_size=5,
            tech_stack="Django, PostgreSQL, React",
            infrastructure_type="Cloud (Azure)",
            status="At Risk",
            cpu_utilization=45,
            memory_utilization=51,
            storage_utilization=48,
            network_utilization=39,
            server_availability=99.9,
            security_incidents=1,
            customer_satisfaction=81,
            unresolved_issues=9,
            dependency_delays=2,
        ),
        dict(
            name="SaaS Inventory Manager",
            description="Multi-tenant SaaS inventory and logistics management tool.",
            industry="SaaS",
            budget=180000,
            current_spending=95000,
            start_date=today - timedelta(days=60),
            expected_end_date=today + timedelta(days=120),
            progress=35,
            expected_progress=30,
            team_size=4,
            tech_stack="Flask, Vue.js, MySQL",
            infrastructure_type="Cloud (GCP)",
            status="On Track",
            cpu_utilization=33,
            memory_utilization=40,
            storage_utilization=28,
            network_utilization=25,
            server_availability=99.8,
            security_incidents=0,
            customer_satisfaction=88,
            unresolved_issues=3,
            dependency_delays=0,
        ),
    ]

    for data in sample_projects:
        db.session.add(Project(**data))

    db.session.commit()

    # Now generate initial risks / history for each seeded project
    from services.risk_engine import analyze_project
    from models.project import Project as ProjectModel
    from models.risk import RiskHistory

    for project in ProjectModel.query.all():
        risks = analyze_project(project)
        for r in risks:
            db.session.add(r)
        db.session.commit()

        from services.analytics_engine import calculate_health_scores
        health = calculate_health_scores(project)
        db.session.add(RiskHistory(
            project_id=project.id,
            risk_score=health["overall_risk_score"],
            health_score=health["overall_health"],
        ))
    db.session.commit()
