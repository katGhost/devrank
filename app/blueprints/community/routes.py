from flask import g, flash, jsonify, redirect, request, render_template, url_for, session
from app.models import User
from app.services.forum_service import get_all_posts, create_post
from app.blueprints.community import forum_bp


# Get all posts
@forum_bp.route('/')
def forum_home():
    
    posts = get_all_posts()
    print(post for post in posts)

    return render_template('forum.html', posts=posts)


# Post creation
@forum_bp.route('/create', methods=['GET', 'POST'])
def new_post():
    
    user = User.query.get(session.get('user_id'))
    
    # Check user exist or is in the session | session expiration
    if 'user_id' not in session and not user:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        # Add category for post belonging -> Python, Java, etc.
        
        if not title or not description:
            flash('Title and description are required', 'danger')
            return render_template('create_post.html', user=user)
        
        post = create_post(
            user_id=user.id,
            title=title,
            body=description
        )
        
        return redirect(url_for('forum.forum_home', post_id=post.id))
    return render_template('create_post.html', user=user)

