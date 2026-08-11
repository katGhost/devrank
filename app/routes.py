from functools import wraps
import requests
from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash
from cachetools import Cache
from app.oauth import oauth
from app.config import Config
from app.extensions import db
from authlib.jose import jwt
from app.models import User, Roadmap
from app.services.leaderboard_service import get_leaderboard
from app.services.ai_service import generate_next_projects
from app.services.github_service import GithubService
from app.services.token_vault_service import get_github_token_from_vault, connect_github_account

cache = Cache(config={'CACHE_TYPE': 'simple'})


app_bp = Blueprint('app', __name__)


@app_bp.route('/')
def home():
    return render_template('index.html')


@app_bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('app.home'))

    user = User.query.get(session.get('user_id'))
    suggestions = []

    if user.github_username:
        # fetch roadmap from DB regardless of token vault status
        # token vault is only needed for generate-roadmap, not for reading saved data
        try:
            suggestions = Roadmap.query.filter_by(
                user_id=user.id
            ).order_by(Roadmap.created_at.desc()).limit(3).all()
        except Exception as e:
            raise Exception("Error fetching roadmap from DB: ", str(e))

    return render_template('dashboard.html', user=user, suggestions=suggestions)


@app_bp.route("/generate-roadmap", methods=["POST"])
def generate_roadmap():
    if 'user_id' not in session:
        return redirect(url_for('app.home'))

    user = User.query.get(session.get('user_id'))

    if user.github_username:
        try:
            # try vault first, fall back to DB token
            github_token = get_github_token_from_vault(user.auth0_id)
            if not github_token:
                print("Token Vault unavailable, using DB token")
                github_token = user.github_token

            if not github_token:
                print("No GitHub token available")
                return redirect(url_for('app.dashboard'))

            github = GithubService(github_token)
            user_activity = github.summarize_user_activity(github_token)
            suggestions = generate_next_projects(user_activity)

            # clear old roadmap
            Roadmap.query.filter_by(user_id=user.id).delete()

            for project in suggestions:
                new_project = Roadmap(
                    user_id=user.id,
                    title=project["title"],
                    description=project["description"],
                    learning_outcome=project.get("learning_outcome", "")
                )
                db.session.add(new_project)

            db.session.commit()

        except Exception as e:
            db.session.rollback()

    return redirect(url_for('app.dashboard'))


@app_bp.route('/leaderboard', methods=['GET'])
@cache.cached(timeout=300)
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('app.home'))

    # Fetch and display all users ranked by comprehensive scoring
    rankings = get_leaderboard()
    return render_template('leaderboard.html', users=rankings)


@app_bp.route('/login', methods=['GET', 'POST'])
def login():
    redirect_uri = url_for('app.callback', _external=True)
    return oauth.auth0.authorize_redirect(redirect_uri)


@app_bp.route('/callback', methods=['GET', 'POST'])
def callback():
    token = oauth.auth0.authorize_access_token()
    session['auth_token'] = token

    # print("FULL TOKEN:", token)
    # print("USERINFO FROM TOKEN:", token.get('userinfo'))
    import os
    domain = os.getenv("AUTH0_DOMAIN")

    resp = oauth.auth0.get(
        f'https://{domain}/userinfo',
        token=token
    )
    user_info = resp.json()

    # upsert user into DB
    auth0_id = user_info.get('sub')
    user = User.query.filter_by(auth0_id=auth0_id).first()

    # if user in the db ->
    if not user:
        # first time login, create user
        user = User(
            auth0_id=auth0_id,
            name=user_info.get('name'),
            email=user_info.get('email'),
            picture=user_info.get('picture'),
            nickname=user_info.get('nickname'),
        )
        db.session.add(user)
    else:
        # returning user, update their info
        user.name = user_info.get('name')
        user.email = user_info.get('email')
        user.picture = user_info.get('picture')
        user.nickname = user_info.get('nickname')
    
    db.session.commit()

    # storing only the db user_id in session
    session['user_id'] = user.id

    return redirect(url_for('app.profile'))


@app_bp.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('app.home'))

    user = User.query.get(session.get('user_id'))
    # print(f'USER FROM DB: ', user)
    # do something about the user info display and storage
    return render_template('profile.html', user=user)


@app_bp.route('/connect/github')
def github_login():
    # only Auth0 logged-in users can connect to github
    # Good for token vault -> Auth0 needs a logged-in user identity to associate the stored GitHub token against
    if 'user_id' not in session:
        return redirect(url_for('app.home'))
    
    redirect_uri = url_for('app.github_callback', _external=True)
    # print('GITHUB REDIRECT: ', redirect_uri)
    return oauth.github.authorize_redirect(redirect_uri)


@app_bp.route('/github/callback')
def github_callback():
    print("GITHUB CALLBACK HIT")
    if 'user_id' not in session:
        return redirect(url_for('app.home'))

    token = oauth.github.authorize_access_token()
    github_token = token['access_token']

    # fetch github username
    headers = {'Authorization': f'Bearer {github_token}'}
    resp = requests.get('https://api.github.com/user', headers=headers)
    github_user = resp.json()

    user = User.query.get(session.get('user_id'))
    if not user:
        return redirect(url_for('app.home'))

    # github username still stored in DB -> not the token
    user.github_username = github_user.get('login')
    db.session.commit()

    # token now stored in Auth0 Token Vault instead of DB
    connected = connect_github_account(user.auth0_id, github_token)
    if connected:
        print("GitHub token stored in Token Vault")
    else:
        # fallback to DB if vault fails -> keeps app working long enough
        user.github_token = github_token
        db.session.commit()

    return redirect(url_for('app.profile'))


# Disconnect github route
@app_bp.route('/disconnect/github', methods=['POST'])
def disconnect_github():
    if 'user_id' not in session:
        return redirect(url_for('app.home'))

    user = User.query.get(session.get('user_id'))
    if not user:
        return redirect(url_for('app.home'))

    # clear github data from DB
    user.github_token = None
    user.github_username = None
    db.session.commit()

    # clear roadmap data tied to this user
    Roadmap.query.filter_by(user_id=user.id).delete()
    db.session.commit()

    return redirect(url_for('app.profile'))


@app_bp.route('/logout')
def logout():
    session.pop('user_info', None)  # fixed key
    session.pop('auth_token', None)
    session.pop('github_token', None)
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('app.home'))  # fixed blueprint prefix