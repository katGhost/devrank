from app.extensions import db
from app.models import Project, ProjectMember, User


def get_all_projects():
    return Project.query.order_by(Project.created_at.desc()).all()


def get_project_by_id(project_id):
    return Project.query.get(project_id)


def create_project(owner_id, title, description):
    project = Project(
        title=title.strip(),
        description=description.strip(),
        owner_id=owner_id,
    )
    db.session.add(project)
    db.session.flush()

    # owner is automatically the first member
    membership = ProjectMember(project_id=project.id, user_id=owner_id)
    db.session.add(membership)
    db.session.commit()
    return project


def join_project(project_id, user_id):
    project = Project.query.get(project_id)
    if not project:
        return False, 'Project not found.'

    if project.is_member(user_id):
        return False, 'You are already a member of this project.'

    if project.is_full():
        limit = project.member_limit()
        return False, f'This project is full. The limit is {limit} members.'

    membership = ProjectMember(project_id=project_id, user_id=user_id)
    db.session.add(membership)
    db.session.commit()
    return True, 'You have joined the project.'


def leave_project(project_id, user_id):
    project = Project.query.get(project_id)
    if not project:
        return False, 'Project not found.'

    if project.owner_id == user_id:
        return False, 'You are the project owner. Delete the project instead of leaving it.'

    membership = ProjectMember.query.filter_by(
        project_id=project_id, user_id=user_id
    ).first()

    if not membership:
        return False, 'You are not a member of this project.'

    db.session.delete(membership)
    db.session.commit()
    return True, 'You have left the project.'


def delete_project(project_id, user_id):
    project = Project.query.get(project_id)
    if not project:
        return False, 'Project not found.'

    if project.owner_id != user_id:
        return False, 'Only the project owner can delete this project.'

    db.session.delete(project)
    db.session.commit()
    return True, 'Project deleted.'


def get_project_members(project_id):
    memberships = ProjectMember.query.filter_by(project_id=project_id).all()
    return [m.user for m in memberships]