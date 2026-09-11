from flask import g, flash, jsonify, redirect, render_template, url_for, session
from app.blueprints.leaderboard import lead_bp
from app.services.leaderboard_service import get_leaderboard


@lead_bp.route('/leaderboard', methods=['GET'])
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    # Fetch and display all users ranked by comprehensive scoring
    rankings = get_leaderboard()
    return render_template('leaderboard.html', users=rankings)

