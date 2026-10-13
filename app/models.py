from datetime import datetime, timedelta
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
    comments = db.relationship('Comment', back_populates='user')

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
    body = db.Column(db.Text, nullable=False)
    issue_address = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='posts')
    forum = db.relationship('Forum', back_populates='posts')
    comments = db.relationship('Comment', back_populates='post', lazy='dynamic')

    def __repr__(self):
        return f"<Post id={self.id} title={self.title}>"


# Belonging | Forums
class Forum(db.Model):
    __tablename__ = 'forums'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True)
    slug = db.Column(db.String(128), unique=True)

    posts = db.relationship('Post', back_populates='forum')
    
    def __repr__(self):
        return f"<Forum id={self.id} name={self.name}>"


class Comment(db.Model):
    __tablename__ = 'forum_comments'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Self-referential for threaded replies
    parent_id = db.Column(db.Integer, db.ForeignKey('forum_comments.id'), nullable=True, index=True)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    # Relationships
    user = db.relationship('User', back_populates='comments')
    post = db.relationship('Post', back_populates='comments')

    def __repr__(self):
        return f"<Comment id={self.id} post_id={self.post_id}>"


# Belonging | Hackathons
class Hackathon(db.Model):
    __tablename__ = 'hackathons'

    id = db.Column(db.Integer, primary_key=True)

    # Where this record came from, so more sources can be added later
    # without breaking existing rows.
    source = db.Column(db.String(32), nullable=False, default='devpost')
    external_id = db.Column(db.String(64), nullable=False)

    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(512), nullable=False, unique=True, index=True)
    organization_name = db.Column(db.String(255), nullable=True)
    location_label = db.Column(db.String(255), nullable=True)
    is_virtual = db.Column(db.Boolean, default=False, nullable=False)
    is_in_person = db.Column(db.Boolean, default=False, nullable=False)
    region = db.Column(db.String(64), nullable=True, index=True)

    # 'upcoming' | 'open' | 'ended' -- taken directly from the source
    open_state = db.Column(db.String(32), nullable=False, default='upcoming', index=True)

    submission_period_dates = db.Column(db.String(128), nullable=True)
    prize_amount = db.Column(db.String(128), nullable=True)
    themes = db.Column(db.String(255), nullable=True)
    thumbnail_url = db.Column(db.String(512), nullable=True)

    # first_seen_at stands in for "published": the source API does not expose
    # a listing date, so recency is measured from when our own scraper first
    # discovered the hackathon. last_seen_at is refreshed on every scrape a
    # hackathon still appears in, so stale/delisted rows can be pruned.
    first_seen_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    last_seen_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('source', 'external_id', name='uq_hackathon_source_external_id'),
    )

    def is_recent(self, days=14):
        return (datetime.utcnow() - self.first_seen_at) <= timedelta(days=days)

    def is_open(self):
        return self.open_state in ('open', 'upcoming')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'organization_name': self.organization_name,
            'location_label': self.location_label,
            'is_virtual': self.is_virtual,
            'is_in_person': self.is_in_person,
            'region': self.region,
            'open_state': self.open_state,
            'submission_period_dates': self.submission_period_dates,
            'prize_amount': self.prize_amount,
            'themes': self.themes,
            'thumbnail_url': self.thumbnail_url,
            'first_seen_at': self.first_seen_at.isoformat(),
            'is_recent': self.is_recent(),
        }

    def __repr__(self):
        return f"<Hackathon id={self.id} title={self.title}>"

