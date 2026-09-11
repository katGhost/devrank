from flask import Blueprint

lead_bp = Blueprint('lead', __name__, url_prefix='/leaderboard')

from app.blueprints.leaderboard import routes