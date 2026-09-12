from flask import Blueprint

projects_bp = Blueprint('project', __name__, template_folder='templates', static_folder='static')

from app.blueprints.projects import routes