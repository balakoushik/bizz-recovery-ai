from flask import Blueprint, render_template
from database.database import db
from models.project import Project
from models.risk import Risk

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    projects = Project.query.all()
    return render_template("dashboard.html", projects=projects)
