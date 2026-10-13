from flask import Blueprint

hackathons_bp = Blueprint('hackathons', __name__, template_folder='templates', static_folder='static')

from app.blueprints.hackathons import routes
