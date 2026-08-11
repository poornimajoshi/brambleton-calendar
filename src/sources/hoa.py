"""Brambleton HOA community events (CivicPlus RSS), filtered to kid/family events."""

import config
from filters import is_kid_relevant
from models import Event
from sources import civicplus


def fetch() -> list[Event]:
    return civicplus.fetch(config.HOA_RSS, "hoa", is_kid_relevant)
