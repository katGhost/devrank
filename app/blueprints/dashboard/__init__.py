from flask import Blueprint

dash_bp = Blueprint('dash', __name__, url_prefix='/dashboard')

from app.blueprints.dashboard import routes