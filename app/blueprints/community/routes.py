from flask import g, flash, jsonify, redirect, render_template, url_for, session
from app.blueprints.community import forum_bp


@forum_bp.route('/')
def forum_home():
    return render_template('forum.html')


# Post creation
@forum_bp.route('/new', methods=['POST'])
def new_post():
    return '<h2>New Post!</h2>'