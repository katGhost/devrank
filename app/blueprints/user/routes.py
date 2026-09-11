from flask import g, flash, jsonify, redirect, render_template, url_for, session
from app.extensions import db
from app.models import User, Roadmap
from app.blueprints.auth import oauth
from app.services.token_vault_service import connect_github_account
from app.blueprints.user import user_bp
import requests


@user_bp.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('app.home'))

    user = User.query.get(session.get('user_id'))
    # print(f'USER FROM DB: ', user)
    # do something about the user info display and storage
    return render_template('profile.html', user=user)


@user_bp.route('/connect/github')
def github_login():
    # only Auth0 logged-in users can connect to github
    # Good for token vault -> Auth0 needs a logged-in user identity to associate the stored GitHub token against
    if 'user_id' not in session:
        return redirect(url_for('app.home'))
    
    redirect_uri = url_for('app.github_callback', _external=True)
    # print('GITHUB REDIRECT: ', redirect_uri)
    return oauth.github.authorize_redirect(redirect_uri)


@user_bp.route('/github/callback')
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
@user_bp.route('/disconnect/github', methods=['POST'])
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


