from flask import Blueprint

community_bp = Blueprint('community', __name__, template_folder='templates', static_folder='static')

from app.blueprints.community import routes