from flask import g, flash, jsonify, redirect, request, render_template, url_for, session
from app.models import User, Forum
from app.services.forum_service import get_all_posts, create_post, get_python_forum, forum_names
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
    forums = Forum.query.all()
    forum_id = [f.id for f in forums if f.name in forum_names]
    
    # Check user exist or is in the session | session expiration
    if 'user_id' not in session and not user:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        forum_name = request.form.get('forum', '').strip()
        description = request.form.get('description', '').strip()
        
        # Add category for post belonging -> Python, Java, etc.
        
        if not title or not description or not forum_name:
            flash('All fields are required', 'danger')
            return render_template('create_post.html', user=user)
        
        post = create_post(
            user_id=user.id,
            forum_id=forum_id,
            title=title,
            forum=forum_name,
            body=description
        )
        
        return redirect(url_for('forum.forum_home', post_id=post.id))
    return render_template('create_post.html', user=user)


# Forum-based postings
@forum_bp.route('/community/python')
def forum_python():
    if request.method == 'POST':
        py_posts = get_python_forum()
        return render_template('forum_python.html', posts=py_posts)
    return redirect(url_for('forum.forum_home'))