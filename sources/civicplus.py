"""Shared parser for CivicPlus calendar RSS feeds (HOA and county)."""

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Callable

import requests

import config
from models import Event
from sources.util import TZ, strip_html

_EID_RE = re.compile(r"EID=(\d+)")
_DATE_FMT = "%B %d, %Y"
_TIME_FMT = "%I:%M %p"


def _child_text(item: ET.Element, local_name: str) -> str:
    """Read a child element by local tag name, ignoring XML namespaces."""
    for child in item:
        if child.tag.rsplit("}", 1)[-1] == local_name:
            return (child.text or "").replace("\xa0", " ").strip()
    return ""


def _combine(date_str: str, time_str: str) -> datetime:
    d = datetime.strptime(date_str.strip(), _DATE_FMT)
    t = datetime.strptime(time_str.strip(), _TIME_FMT).time()
    return datetime.combine(d.date(), t, tzinfo=TZ)


def _parse_when(dates: str, times: str):
    """Return (start, end, all_day) from CivicPlus date/time strings."""
    date_parts = [p.strip() for p in dates.split(" - ") if p.strip()]
    start_date = date_parts[0]
    end_date = date_parts[1] if len(date_parts) > 1 else start_date

    times = times.strip()
    if not times or "all day" in times.lower():
        start = datetime.strptime(start_date, _DATE_FMT).replace(tzinfo=TZ)
        end = datetime.strptime(end_date, _DATE_FMT).replace(tzinfo=TZ)
        return start, end, True

    time_parts = [p.strip() for p in times.split("-") if p.strip()]
    start = _combine(start_date, time_parts[0])
    if len(time_parts) > 1:
        end = _combine(end_date, time_parts[1])
    else:
        end = start + timedelta(hours=1)
    return start, end, False


def fetch(url: str, source: str, relevant: Callable[[str], bool]) -> list[Event]:
    resp = requests.get(url, headers={"User-Agent": config.USER_AGENT}, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    events: list[Event] = []
    for item in root.findall(".//item"):
        title = _child_text(item, "title")
        link = _child_text(item, "link")
        location = strip_html(_child_text(item, "Location"))
        description = strip_html(_child_text(item, "description"))

        if not relevant(f"{title} {location} {description}"):
            continue

        dates = _child_text(item, "EventDates")
        if not dates:
            continue
        try:
            start, end, all_day = _parse_when(dates, _child_text(item, "EventTimes"))
        except ValueError:
            continue

        eid = _EID_RE.search(link)
        uid = eid.group(1) if eid else str(abs(hash((title, dates))))

        events.append(
            Event(
                source=source,
                uid=uid,
                title=title,
                start=start,
                end=end,
                all_day=all_day,
                url=link,
                location=location,
                description=description,
            )
        )
    return events
