from flask import render_template, request, redirect, url_for, session, jsonify

from app.blueprints.hackathons import hackathons_bp
from app.services.hackathon_service import get_hackathons, get_available_regions
from app.services.forum_service import get_all_forums

VALID_MODES = ('virtual', 'in_person')


def _parse_filters():
    region = request.args.get('region') or None
    mode = request.args.get('mode') or None
    if mode not in VALID_MODES:
        mode = None
    return region, mode


@hackathons_bp.route('/')
def hackathons_home():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))

    region, mode = _parse_filters()

    hackathons = get_hackathons(region=region, mode=mode)
    regions = get_available_regions()
    forums = get_all_forums()

    return render_template(
        'hackathons.html',
        hackathons=hackathons,
        regions=regions,
        selected_region=region,
        selected_mode=mode,
        forums=forums,
        active_tab='hackathons',
        active_category=None,
    )


@hackathons_bp.route('/api')
def hackathons_api():
    """Simple JSON feed of currently open hackathons, newest first."""
    if 'user_id' not in session:
        return jsonify({'error': 'authentication required'}), 401

    region, mode = _parse_filters()
    hackathons = get_hackathons(region=region, mode=mode)

    return jsonify({
        'count': len(hackathons),
        'region': region,
        'mode': mode,
        'hackathons': [h.to_dict() for h in hackathons],
    })
