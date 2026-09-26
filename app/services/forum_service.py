from app.extensions import db
from app.models import User, Post
from datetime import datetime
from slugify import slugify


# get all forum posts
def get_all_posts():
    """Queries and returns all users posts for feed rendering"""
    posts = Post.query.order_by(Post.created_at.desc())
    
    if not posts:
        return False, 'No posts to display. Create a post'
    
    # slugify posts
    # for post in posts:
    #     post['slug'] = slugify(post['title'])
    #     post['created_at'] = datetime.strptime(post['created_at'], '%d%m%y - %H:%M:%S')

    return posts


# create a forum post
def create_post(user_id, title, body):
    post = Post(
        user_id=user_id,
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

