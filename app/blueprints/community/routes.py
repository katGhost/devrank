from flask import g, flash, jsonify, redirect, render_template, url_for, session
from app.blueprints.community import community_bp


@community_bp.route('/')
def community_forum():
    return render_template('forum.html')