import os
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import Flask
from dotenv import load_dotenv

load_dotenv('.env', override=True)
# blueprints imports
from app.blueprints.main import main_bp
from app.blueprints.auth import auth_bp
from app.blueprints.dashboard import dash_bp
from app.blueprints.leaderboard import lead_bp
from app.blueprints.user import user_bp
from app.blueprints.community import forum_bp
from app.blueprints.projects import projects_bp
from app.blueprints.auth.oauth import init_oauth
from app.extensions import db, migrate


def create_app():
    app = Flask(__name__)

    # Config FIRST
    app.config.from_object('app.config.Config')

    app.secret_key = app.config['SECRET_KEY']
    
    app.config['PREFERRED_URL_SCHEME'] = 'https'    # still in dev
    app.config.update(
        SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    # Initialize extensions
    db.init_app(app)
    init_oauth(app)
    
    migrate.init_app(app, db)
    

    # Register blueprints
    app.register_blueprint(main_bp, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dash_bp, url_prefix='/dashboard')
    app.register_blueprint(lead_bp, url_prefix='/rankings')
    app.register_blueprint(forum_bp, url_prefix='/community')
    app.register_blueprint(projects_bp, url_prefix='/projects')
    app.register_blueprint(user_bp, url_prefix='/user')

    # Create tables if they do not exist
    with app.app_context():
        db.create_all()

    # ProxyFix LAST, after everything is configured
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    return app


