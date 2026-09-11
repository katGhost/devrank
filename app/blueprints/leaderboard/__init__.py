from flask import Blueprint

lead_bp = Blueprint('lead', __name__, template_folder='templates', static_folder='static')

from app.blueprints.leaderboard import routes