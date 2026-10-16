import requests
from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from app.blueprints.projects import projects_bp
from app.extensions import db
from app.models import User, Roadmap, Project, ProjectMember
from app.services.projects_service import (
    get_all_projects,
    get_project_by_id,
    create_project,
    join_project,
    leave_project,
    delete_project,
    get_project_members,
)
from app.services.scaffold_service import get_supported_stacks, scaffold_project_to_github, ScaffoldError
from app.services.token_vault_service import get_github_token_from_vault


@projects_bp.route('/')
def projects_hub():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user = User.query.get(session.get('user_id'))
    all_projects = get_all_projects()
    return render_template('projects.html', user=user, projects=all_projects)


@projects_bp.route('/<int:project_id>/scaffold', methods=['POST'])
def project_scaffold(project_id):
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user = User.query.get(session.get('user_id'))
    project = get_project_by_id(project_id)

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('project.projects_hub'))

    if project.owner_id != user.id:
        flash('Only the project owner can scaffold this project.', 'danger')
        return redirect(url_for('project.project_detail', project_id=project_id))

    if project.is_scaffolded():
        flash('This project already has a scaffolded repo.', 'warning')
        return redirect(url_for('project.project_detail', project_id=project_id))

    if not user.github_username:
        flash('Connect GitHub before scaffolding this project.', 'warning')
        return redirect(url_for('project.project_detail', project_id=project_id))

    if not project.tech_stack:
        submitted_stack = request.form.get('tech_stack')
        if not submitted_stack or submitted_stack not in dict(get_supported_stacks()):
            flash('Choose a tech stack to scaffold this project with.', 'warning')
            return redirect(url_for('project.project_detail', project_id=project_id))
        project.tech_stack = submitted_stack

    github_token = get_github_token_from_vault(user.auth0_id)
    if not github_token:
        print("Token Vault unavailable, using DB token")
        github_token = user.github_token

    if not github_token:
        flash('Could not access your GitHub token. Reconnect GitHub and try again.', 'danger')
        return redirect(url_for('project.project_detail', project_id=project_id))

    try:
        repo_url = scaffold_project_to_github(github_token, user.github_username, project)
    except ScaffoldError as e:
        flash(str(e), 'danger')
        return redirect(url_for('project.project_detail', project_id=project_id))

    project.github_repo_url = repo_url
    db.session.commit()
    flash('Project scaffolded to GitHub.', 'success')
    return redirect(url_for('project.project_detail', project_id=project_id))


@projects_bp.route('/new', methods=['GET', 'POST'])
def project_new():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user = User.query.get(session.get('user_id'))

    if not user.github_username:
        flash('You must connect your GitHub account before creating a project.', 'warning')
        return redirect(url_for('project.projects_hub'))

    stacks = get_supported_stacks()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        tech_stack = request.form.get('tech_stack') or None

        if not title or not description:
            flash('Title and description are required.', 'danger')
            return render_template('project_new.html', user=user, stacks=stacks)

        if tech_stack and tech_stack not in dict(stacks):
            tech_stack = None

        project = create_project(
            owner_id=user.id,
            title=title,
            description=description,
            tech_stack=tech_stack,
        )
        return redirect(url_for('project.project_detail', project_id=project.id))

    return render_template('project_new.html', user=user, stacks=stacks)


@projects_bp.route('/<int:project_id>')
def project_detail(project_id):
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user = User.query.get(session.get('user_id'))
    project = get_project_by_id(project_id)

    if not project:
        flash('Project not found.', 'danger')
        return redirect(url_for('project.projects_hub'))

    members = get_project_members(project_id)
    is_member = project.is_member(user.id)
    is_owner = project.owner_id == user.id

    return render_template(
        'project_detail.html',
        user=user,
        project=project,
        members=members,
        is_member=is_member,
        is_owner=is_owner,
        stacks=get_supported_stacks(),
    )


@projects_bp.route('/<int:project_id>/join', methods=['POST'])
def project_join(project_id):
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user = User.query.get(session.get('user_id'))

    if not user.github_username:
        flash('You must connect your GitHub account to join a project.', 'warning')
        return redirect(url_for('project.project_detail', project_id=project_id))

    success, message = join_project(project_id, user.id)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('project.project_detail', project_id=project_id))


@projects_bp.route('/<int:project_id>/leave', methods=['POST'])
def project_leave(project_id):
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user = User.query.get(session.get('user_id'))
    success, message = leave_project(project_id, user.id)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('project.project_detail', project_id=project_id))


@projects_bp.route('/<int:project_id>/delete', methods=['POST'])
def project_delete(project_id):
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user = User.query.get(session.get('user_id'))
    success, message = delete_project(project_id, user.id)
    flash(message, 'success' if success else 'danger')

    if success:
        return redirect(url_for('project.projects_hub'))
    return redirect(url_for('project.project_detail', project_id=project_id))