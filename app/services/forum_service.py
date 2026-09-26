from app.extensions import db
from app.models import User, Post, Forum
from datetime import datetime
from slugify import slugify


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
    
    if python_forum not in forum_names:
        return False, 'Forum does not exist'

    posts = python_forum.posts
    return posts


# create a forum post
def create_post(user_id, forum_id, title, forum, body):
    
    forum = Forum.query.filter_by(id=forum_id).first() 
    
    post = Post(
        user_id=user_id,
        forum_id=forum.id,
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

