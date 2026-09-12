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


@projects_bp.route('/')
def projects_hub():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user = User.query.get(session.get('user_id'))
    all_projects = get_all_projects()
    return render_template('projects.html', user=user, projects=all_projects)


@projects_bp.route('/new', methods=['GET', 'POST'])
def project_new():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user = User.query.get(session.get('user_id'))

    if not user.github_username:
        flash('You must connect your GitHub account before creating a project.', 'warning')
        return redirect(url_for('project.projects_hub'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()

        if not title or not description:
            flash('Title and description are required.', 'danger')
            return render_template('project_new.html', user=user)

        project = create_project(
            owner_id=user.id,
            title=title,
            description=description,
        )
        return redirect(url_for('project.project_detail', project_id=project.id))

    return render_template('project_new.html', user=user)


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