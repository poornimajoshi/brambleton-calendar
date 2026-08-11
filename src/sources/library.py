"""Brambleton Library events (Communico backend), filtered to ages 3-5."""

import json
from datetime import datetime

import requests

import config
from models import Event
from sources.util import TZ, local_dt, strip_html


def _parse(value: str) -> datetime:
    return local_dt(value, "%Y-%m-%d %H:%M:%S")


def fetch() -> list[Event]:
    req = {
        "date": datetime.now(TZ).strftime("%Y-%m-%d"),
        "days": config.LOOKAHEAD_DAYS,
        "private": False,
    }
    resp = requests.get(
        config.LIBRARY_API,
        params={"event_type": "0", "req": json.dumps(req)},
        headers={"User-Agent": config.USER_AGENT},
        timeout=30,
    )
    resp.raise_for_status()

    events: list[Event] = []
    for e in resp.json():
        if e.get("location") != config.LIBRARY_BRANCH:
            continue
        if config.LIBRARY_AGE_LABEL not in (e.get("agesArray") or []):
            continue
        if str(e.get("changed")) == "1":  # cancelled
            continue

        start = _parse(e.get("raw_start_time") or e["event_start"])
        end = _parse(e.get("raw_end_time") or e["event_end"])
        all_day = (
            start.hour == 0 and start.minute == 0
            and end.hour == 23 and end.minute >= 59
        )

        events.append(
            Event(
                source="library",
                uid=str(e["id"]),
                title=e["title"].strip(),
                start=start,
                end=end,
                all_day=all_day,
                url=e.get("url", ""),
                location=e.get("location", ""),
                description=strip_html(e.get("description", "")),
            )
        )
    return events
