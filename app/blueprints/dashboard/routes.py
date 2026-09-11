from flask import g, flash, jsonify, redirect, render_template, url_for, session
from app.blueprints.dashboard import dash_bp
from app.extensions import db
from app.models import User, Roadmap
from app.services.ai_service import generate_next_projects
from app.services.github_service import GithubService
from app.services.token_vault_service import get_github_token_from_vault



# Dashboard route with roadmap generator
@dash_bp.route('/', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

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


@dash_bp.route("/generate-roadmap", methods=["POST"])
def generate_roadmap():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

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
                return redirect(url_for('dash.dashboard'))

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

    return redirect(url_for('dash.dashboard'))


