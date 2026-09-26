from app.extensions import db
from app.models import User, Post, Forum
from datetime import datetime
from slugify import slugify


FORUM_NAMES = [
    "Python",
    "JavaScript",
    "React",
    "AI",
    "Cloud",
    "Backend",
    "Frontend",
]


def seed_forums():
    """Create default forums if they do not exist. Call once at app startup."""
    for name in FORUM_NAMES:
        existing = Forum.query.filter_by(name=name).first()
        if not existing:
            forum = Forum(name=name, slug=slugify(name))
            db.session.add(forum)
    db.session.commit()


def get_all_forums():
    """Return all forums for sidebar rendering."""
    return Forum.query.all()


def get_all_posts():
    """Return all posts ordered by newest first."""
    return Post.query.order_by(Post.created_at.desc()).all()


def get_forum_posts(forum_name):
    """Return posts for a named forum, or an error tuple if it does not exist."""
    forum = Forum.query.filter_by(name=forum_name).first()
    if not forum:
        return False, 'Forum does not exist'
    posts = Post.query.filter_by(forum_id=forum.id).order_by(Post.created_at.desc()).all()
    return posts, None


def get_trending_posts(limit=5):
    """Return the most recent posts across all forums for the trending panel."""
    return Post.query.order_by(Post.created_at.desc()).limit(limit).all()


def get_post(post_id):
    """Return a single post by id."""
    return db.session.get(Post, post_id)


def create_post(user_id, forum_id, title, body, issue_address=None):
    """Create and persist a new post. Returns the post or an error tuple."""
    forum_record = db.session.get(Forum, forum_id)
    if not forum_record:
        return False, 'Forum does not exist'
    if not title or not title.strip():
        return False, 'Post title is required'
    if not body or not body.strip():
        return False, 'Post body is required'

    post = Post(
        user_id=user_id,
        forum_id=forum_record.id,
        title=title.strip(),
        body=body.strip(),
        issue_address=issue_address.strip() if issue_address else None
    )

    db.session.add(post)
    db.session.commit()
    return post, None


def delete_post(post_id, user_id):
    """Delete a post. Only the owner may delete."""
    post = db.session.get(Post, post_id)
    if not post:
        return False, 'Post not found'
    if post.user_id != user_id:
        return False, 'Only the owner can delete this post'

    db.session.delete(post)
    db.session.commit()
    return True, None


def edit_post(post_id, user_id, title, body, issue_address=None):
    """Edit a post. Only the owner may edit."""
    post = db.session.get(Post, post_id)
    if not post:
        return False, 'Post not found'
    if post.user_id != user_id:
        return False, 'Only the owner can edit this post'
    if not title or not title.strip():
        return False, 'Post title is required'
    if not body or not body.strip():
        return False, 'Post body is required'

    post.title = title.strip()
    post.body = body.strip()
    post.issue_address = issue_address.strip() if issue_address else post.issue_address
    db.session.commit()
    return post, None