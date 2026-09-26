from app.extensions import db
from app.models import User, Post, Forum
from datetime import datetime


forum_names = [
    "Python",
    "JavaScript",
    "React",
    "AI",
    "Cloud",
    "Backend",
    "Frontend",
]

# get all forum posts
def get_all_posts():
    """Queries and returns all users posts for feed rendering"""
    posts = Post.query.all()
    
    if not posts:
        return False, 'No posts to display. Create a post'

    return posts


# Get posts by forum
def get_python_forum():
    python_forum = Forum.query.filter_by(name="Python").first()

    if not python_forum:
        return False, 'Forum does not exist'

    return python_forum.posts


def get_forum_posts(forum_name):
    """Return posts for a named forum, or an error if it does not exist."""
    if forum_name not in forum_names:
        return False, 'Forum does not exist'

    forum = Forum.query.filter_by(name=forum_name).first()
    if not forum:
        return False, 'Forum does not exist'

    return forum.posts


# create a forum post
def create_post(user_id, forum_id, title, forum, body):
    forum_record = Forum.query.filter_by(id=forum_id).first()
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
        body=body.strip()
    )
    
    db.session.add(post)
    db.session.commit()
    
    return post

# Delete post
def delete_post(post_id, user_id):
    post = Post.query.get(post_id)
    if not post:
        return False, 'Post not found.'
    
    if post.user_id != user_id:
        return False, 'Only the owner can delete the post'
    
    db.session.delete(post)
    db.session.commit()
    return True, 'Post deleted.'

# Edit post
def edit_post(post_id, user_id, title, body):
    post = Post.query.get(post_id)
    if not post:
        return False, 'Post not found.'

    if post.user_id != user_id:
        return False, 'Only the owner can edit the post'
    if not title or not title.strip():
        return False, 'Post title is required'
    if not body or not body.strip():
        return False, 'Post body is required'

    post.title = title.strip()
    post.body = body.strip()
    db.session.commit()
    return post

