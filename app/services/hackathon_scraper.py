import re
import time
import random
import requests
from cachetools import TTLCache

_TAG_RE = re.compile(r'<[^>]+>')


def _strip_html(value):
    """Devpost embeds markup in a few text fields (e.g. prize_amount);
    strip it so we never store or render raw third-party HTML."""
    if not value:
        return value
    return _TAG_RE.sub('', value).strip()

from app.extensions import db
from app.services.hackathon_service import upsert_hackathon

DEVPOST_API_URL = "https://devpost.com/api/hackathons"
SEARCH_KEYWORDS = ["Africa", "South Africa"]

MAX_RETRIES = 3
REQUEST_TIMEOUT = 10
BASE_BACKOFF_SECONDS = 1.5
REQUEST_DELAY_SECONDS = 1.0   # politeness delay between requests
MAX_PAGES_PER_KEYWORD = 10    # safety cap so a bad response can't loop forever

HEADERS = {
    'User-Agent': (
        'DevRankBot/1.0 (+https://github.com/katGhost/devrank; '
        'hackathon discovery for African developers)'
    ),
    'Accept': 'application/json',
}

# Short-lived in-memory cache so re-running the scraper twice in quick
# succession (e.g. a manual run right after the weekly cron) does not
# re-hit pages it already fetched a few minutes ago.
_page_cache = TTLCache(maxsize=200, ttl=600)


def _get_with_retries(session, params):
    """
    Fetch one page politely.

    Transient failures (timeouts, connection errors, 429, 5xx) are retried
    up to MAX_RETRIES with exponential backoff plus jitter. A 4xx error
    other than 429 is a client error -- retrying will not fix it -- so it
    is logged and skipped instead of hammering the server.
    """
    cache_key = tuple(sorted(params.items()))
    if cache_key in _page_cache:
        return _page_cache[cache_key]

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(
                DEVPOST_API_URL,
                params=params,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 429 or response.status_code >= 500:
                last_error = f"HTTP {response.status_code}"
                raise requests.exceptions.RequestException(last_error)

            if 400 <= response.status_code < 500:
                # e.g. a malformed query or a page past the end -- will not
                # resolve on retry, so skip this page gracefully.
                print(f"Hackathon scraper: client error {response.status_code} for {params}, skipping")
                return None

            response.raise_for_status()
            data = response.json()
            _page_cache[cache_key] = data
            return data

        except (requests.exceptions.RequestException, ValueError) as e:
            last_error = str(e)
            if attempt < MAX_RETRIES:
                backoff = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
                backoff += random.uniform(0, 0.5)  # jitter avoids a thundering herd
                time.sleep(backoff)

    print(f"Hackathon scraper: giving up on {params} after {MAX_RETRIES} attempts ({last_error})")
    return None


def _derive_region(title, organization_name, location_label):
    haystack = " ".join(filter(None, [title, organization_name, location_label])).lower()
    if 'south africa' in haystack:
        return 'South Africa'
    if 'africa' in haystack:
        return 'Africa'
    return None


def _normalize(raw, keyword):
    """Map a raw Devpost hackathon object onto our Hackathon fields."""
    location = (raw.get('displayed_location') or {}).get('location', '') or ''
    is_virtual = location.strip().lower() == 'online'

    region = _derive_region(raw.get('title', ''), raw.get('organization_name', ''), location)
    if not region:
        # Devpost's search is fuzzy, so a result can match the query without
        # literally containing "Africa" in its text. Fall back to the
        # keyword that surfaced it rather than dropping the result.
        region = 'South Africa' if keyword == 'South Africa' else 'Africa'

    theme_names = ", ".join(
        t.get('name', '') for t in (raw.get('themes') or []) if t.get('name')
    )

    return {
        'source': 'devpost',
        'external_id': str(raw['id']),
        'title': (raw.get('title') or '').strip(),
        'url': (raw.get('url') or '').strip(),
        'organization_name': raw.get('organization_name'),
        'location_label': location or None,
        'is_virtual': is_virtual,
        'is_in_person': not is_virtual,
        'region': region,
        'open_state': raw.get('open_state', 'upcoming'),
        'submission_period_dates': raw.get('submission_period_dates'),
        'prize_amount': _strip_html(raw.get('prize_amount')),
        'themes': theme_names or None,
        'thumbnail_url': raw.get('thumbnail_url'),
    }


def _fetch_keyword(session, keyword):
    """Page through every result for one search keyword."""
    results = []
    page = 1

    while page <= MAX_PAGES_PER_KEYWORD:
        data = _get_with_retries(session, {'search': keyword, 'page': page})
        if data is None:
            break

        hackathons = data.get('hackathons', [])
        if not hackathons:
            break

        results.extend(hackathons)

        meta = data.get('meta', {})
        total_count = meta.get('total_count', 0)
        per_page = meta.get('per_page', len(hackathons) or 1)
        if page * per_page >= total_count:
            break

        page += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return results


def scrape_hackathons():
    """
    Weekly entry point: search Devpost for Africa / South Africa hackathons,
    normalize and upsert each into the database.

    Safe to call manually too -- a 400/429/5xx on one keyword or page does
    not stop the others, so a single bad response degrades the run instead
    of failing it outright.

    Returns a summary dict: {'created', 'updated', 'seen', 'errors'}.
    """
    session = requests.Session()
    summary = {'created': 0, 'updated': 0, 'seen': 0, 'errors': 0}
    seen_urls = set()

    for keyword in SEARCH_KEYWORDS:
        try:
            raw_results = _fetch_keyword(session, keyword)
        except Exception as e:
            print(f"Hackathon scraper: unexpected failure on keyword '{keyword}': {e}")
            summary['errors'] += 1
            continue

        for raw in raw_results:
            try:
                url = raw.get('url')
                if not url or url in seen_urls:
                    continue  # dedupe across overlapping keyword searches
                seen_urls.add(url)

                normalized = _normalize(raw, keyword)
                if not normalized['title'] or not normalized['url']:
                    continue

                _, created = upsert_hackathon(normalized)
                summary['seen'] += 1
                summary['created' if created else 'updated'] += 1
            except Exception as e:
                print(f"Hackathon scraper: failed to process result {raw.get('id')}: {e}")
                summary['errors'] += 1

        time.sleep(REQUEST_DELAY_SECONDS)

    db.session.commit()
    return summary
