from flask import render_template
from app.blueprints.main import main_bp

@main_bp.route('/', methods=['GET'])
def home():
    return render_template("index.html")