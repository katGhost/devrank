from datetime import datetime
from app.extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    auth0_id = db.Column(db.String(128), unique=True, nullable=False)

    name = db.Column(db.String(128), nullable=True)
    email = db.Column(db.String(128), nullable=True)
    picture = db.Column(db.String(512), nullable=True)
    nickname = db.Column(db.String(128), nullable=True)
    github_token = db.Column(db.String(256), nullable=True)
    github_username = db.Column(db.String(128), nullable=True)
    is_pro = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relaitionships
    roadmaps = db.relationship('Roadmap', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    posts = db.relationship('Post', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'auth0_id': self.auth0_id,
            'name': self.name,
            'email': self.email,
            'picture': self.picture,
            'nickname': self.nickname,
            'github_username': self.github_username,
        }
    
    def __repr__(self):
        return f"<User id={self.id} auth0_id={self.auth0_id}>"


class Roadmap(db.Model):
    __tablename__ = 'roadmaps'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    learning_outcome = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", back_populates="roadmaps")

    def __repr__(self):
        return f"<Roadmap id={self.id} title={self.title}>"


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    owner = db.relationship('User', foreign_keys=[owner_id], backref=db.backref('owned_projects', lazy='dynamic'))
    members = db.relationship('ProjectMember', back_populates='project', cascade='all, delete-orphan', lazy='dynamic')

    def member_count(self):
        return self.members.count()

    def is_member(self, user_id):
        return self.members.filter_by(user_id=user_id).first() is not None

    def member_limit(self):
        return 15 if self.owner.is_pro else 5

    def is_full(self):
        return self.member_count() >= self.member_limit()

    def __repr__(self):
        return f"<Project id={self.id} title={self.title}>"


class ProjectMember(db.Model):
    __tablename__ = 'project_members'

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', back_populates='members')
    user = db.relationship('User', backref=db.backref('project_memberships', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('project_id', 'user_id', name='uq_project_member'),
    )

    def __repr__(self):
        return f"<ProjectMember project_id={self.project_id} user_id={self.user_id}>"

class Post(db.Model):
    __tablename__ = 'forum_posts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    forum_id = db.Column(db.Integer, db.ForeignKey('forums.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)   # Where does it belong
    issue_address = db.Column(db.Text, nullable=True)   # What have you tried to fix the issue
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='posts')
    forums = db.relationship('Forum', back_populates='posts')

    def __repr__(self):
        return f"<Post id={self.id} title={self.title}>"


# Belonging | Forums
class Forum(db.Model):
    __tablename__ = 'forums'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    
    post = db.relationship('Post', back_populates='forums')
    
    def __repr__(self):
        return f"<Forum id={self.id} name={self.name}>"