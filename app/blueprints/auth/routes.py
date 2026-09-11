from flask import g, flash, jsonify, redirect, render_template, url_for, session
from app.extensions import db
from app.models import User
from app.blueprints.auth import oauth
from app.blueprints.auth import auth_bp



# OAuth login -> Auth0 Google Authentication
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    redirect_uri = url_for('app.callback', _external=True)
    return oauth.auth0.authorize_redirect(redirect_uri)


@auth_bp.route('/callback', methods=['GET', 'POST'])
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


# Logout
@auth_bp.route('/logout')
def logout():
    session.pop('user_info', None)  # fixed key
    session.pop('auth_token', None)
    session.pop('github_token', None)
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('app.home'))  # fixed blueprint prefix
