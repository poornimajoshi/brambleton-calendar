"""Loudoun County parks events (CivicPlus RSS), filtered to Hanson/nature kid events.

Best-effort only: PRCS program registrations (Hal & Berni Hanson Regional Park)
live in WebTrac, which is Cloudflare-protected and not scrapable. This picks up
park/nature kids events only when the county publishes them on its main calendar.
"""

import config
from filters import is_parks_relevant
from models import Event
from sources import civicplus


def fetch() -> list[Event]:
    return civicplus.fetch(config.COUNTY_RSS, "parks", is_parks_relevant)
