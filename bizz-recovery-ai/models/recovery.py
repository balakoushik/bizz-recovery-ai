import json
from datetime import datetime
from database.database import db


class RecoveryPlan(db.Model):
    __tablename__ = "recovery_plans"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_json = db.Column(db.Text, nullable=False)  # JSON-serialized structured plan
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def content(self):
        return json.loads(self.content_json)

    @content.setter
    def content(self, value):
        self.content_json = json.dumps(value)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M"),
        }
