from flask import flash, redirect, request, render_template, url_for, session
from app.models import User, Forum
from app.services.forum_service import (
    get_all_posts, get_forum_posts, get_trending_posts,
    create_post, FORUM_NAMES, get_all_forums, get_all_comments
)

from app.blueprints.community import forum_bp



@forum_bp.route('/')
def forum_home():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    posts = get_all_posts()
    trending_posts = get_trending_posts()
    forums = get_all_forums()
    comments = get_all_comments()

    return render_template(
        'forum.html',
        posts=posts,
        trending_posts=trending_posts,
        active_category=None,
        active_tab='feed',
        forums=forums,
        comments=comments
    )


@forum_bp.route('/create', methods=['GET', 'POST'])
def new_post():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    user = User.query.get(session.get('user_id'))
    forums = Forum.query.all()

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        forum_id = request.form.get('forum_id', '').strip()
        body = request.form.get('description', '').strip()
        issue_address = request.form.get('issue_address', '').strip()

        if not title or not body or not forum_id:
            flash('All fields are required', 'danger')
            return render_template('create_post.html', user=user, forums=forums)

        post, error = create_post(
            user_id=user.id,
            forum_id=int(forum_id),
            title=title,
            body=body,
            issue_address=issue_address or None
        )

        if error:
            flash(error, 'danger')
            return render_template('create_post.html', user=user, forums=forums)

        return redirect(url_for('forum.forum_home'))

    return render_template('create_post.html', user=user, forums=forums)


@forum_bp.route('/<forum_name>')
def forum_posts(forum_name):
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    posts, error = get_forum_posts(forum_name)
    if error:
        flash(error, 'danger')
        return redirect(url_for('forum.forum_home'))

    trending_posts = get_trending_posts()
    forums = get_all_forums()

    return render_template(
        'forum.html',
        posts=posts,
        trending_posts=trending_posts,
        active_category=forum_name,
        active_tab='feed',
        forums=forums
    )
