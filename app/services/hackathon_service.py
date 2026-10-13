from datetime import datetime, timedelta
from app.extensions import db
from app.models import Hackathon

RECENT_WINDOW_DAYS = 14
OPEN_STATES = ('open', 'upcoming')


def upsert_hackathon(data):
    """
    Create or update a hackathon from normalized scraper data.
    Matched on (source, external_id). first_seen_at is set once and never
    touched again -- it is our proxy for "published". last_seen_at is
    refreshed every time the scraper still finds the listing.
    Returns (hackathon, created).
    """
    existing = Hackathon.query.filter_by(
        source=data['source'],
        external_id=data['external_id']
    ).first()
    now = datetime.utcnow()

    if existing:
        existing.title = data['title']
        existing.url = data['url']
        existing.organization_name = data.get('organization_name')
        existing.location_label = data.get('location_label')
        existing.is_virtual = data.get('is_virtual', False)
        existing.is_in_person = data.get('is_in_person', False)
        existing.region = data.get('region')
        existing.open_state = data.get('open_state', existing.open_state)
        existing.submission_period_dates = data.get('submission_period_dates')
        existing.prize_amount = data.get('prize_amount')
        existing.themes = data.get('themes')
        existing.thumbnail_url = data.get('thumbnail_url')
        existing.last_seen_at = now
        return existing, False

    hackathon = Hackathon(
        source=data['source'],
        external_id=data['external_id'],
        title=data['title'],
        url=data['url'],
        organization_name=data.get('organization_name'),
        location_label=data.get('location_label'),
        is_virtual=data.get('is_virtual', False),
        is_in_person=data.get('is_in_person', False),
        region=data.get('region'),
        open_state=data.get('open_state', 'upcoming'),
        submission_period_dates=data.get('submission_period_dates'),
        prize_amount=data.get('prize_amount'),
        themes=data.get('themes'),
        thumbnail_url=data.get('thumbnail_url'),
        first_seen_at=now,
        last_seen_at=now,
    )
    db.session.add(hackathon)
    return hackathon, True


def get_hackathons(region=None, mode=None, recent_only=False, open_only=True):
    """
    Return hackathons ordered newest-first (first_seen_at desc), so recently
    discovered ones are always at the top regardless of which filters apply.

    region: exact match against Hackathon.region (e.g. 'Africa', 'South Africa'),
            or None for all regions.
    mode: 'virtual', 'in_person', or None for both.
    recent_only: restrict to hackathons first seen within RECENT_WINDOW_DAYS.
    open_only: exclude hackathons whose open_state is 'ended' (default True).
    """
    query = Hackathon.query

    if open_only:
        query = query.filter(Hackathon.open_state.in_(OPEN_STATES))
    if region:
        query = query.filter(Hackathon.region == region)
    if mode == 'virtual':
        query = query.filter(Hackathon.is_virtual.is_(True))
    elif mode == 'in_person':
        query = query.filter(Hackathon.is_in_person.is_(True))
    if recent_only:
        cutoff = datetime.utcnow() - timedelta(days=RECENT_WINDOW_DAYS)
        query = query.filter(Hackathon.first_seen_at >= cutoff)

    return query.order_by(Hackathon.first_seen_at.desc()).all()


def get_available_regions():
    """Return distinct regions currently present, to populate the filter dropdown."""
    rows = (
        db.session.query(Hackathon.region)
        .filter(Hackathon.region.isnot(None))
        .distinct()
        .all()
    )
    return sorted(r[0] for r in rows)


def prune_stale(days=60):
    """
    Remove hackathons the scraper has not seen in `days`, e.g. delisted or
    expired entries. Not run automatically -- call from the CLI if the table
    needs cleaning up.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    stale = Hackathon.query.filter(Hackathon.last_seen_at < cutoff).all()
    for hackathon in stale:
        db.session.delete(hackathon)
    db.session.commit()
    return len(stale)
