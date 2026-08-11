"""Shared prompt + parsing for the LLM-backed parks source.

WebTrac (the real registration system) is Cloudflare-blocked, so a web-search
capable model is asked to find published children's programs at Hal & Berni
Hanson Regional Park and return them as structured JSON. Provider modules
(parks_gpt, parks_gemini) supply the raw model text; this module builds the
Events with guardrails: anything without an explicit in-window date and a
source URL is dropped.
"""

import json
from datetime import datetime, timedelta

import config
from models import Event
from sources.util import TZ, local_dt

_PROMPT = """\
Find children's events and programs suitable for ages 3-5 taking place at
Hal & Berni Hanson Regional Park (including the Hanson Nature Center) in
Aldie/Brambleton, Loudoun County, Virginia, within the next {days} days.
Today is {today}. Search loudoun.gov, the PRCS Activity Guide, PRCS Connect,
and the park's nature center pages.

Return ONLY a JSON array (no prose, no code fences). Each item must be:
{{"title": str, "date": "YYYY-MM-DD", "start_time": "HH:MM" (24h) or null,
  "end_time": "HH:MM" (24h) or null, "location": str, "url": str, "description": str}}

Rules:
- Only include events with a specific calendar date within the window.
- Only include events you actually found on a real page; put that page in "url".
- If you are unsure of the date, omit the event. Do not invent events.
- Focus on ages 3-5 (toddler, preschool, nature explorer, storytime, family).
"""


def prompt() -> str:
    return _PROMPT.format(days=config.LOOKAHEAD_DAYS, today=datetime.now(TZ).date())


def _parse_json(text: str) -> list[dict]:
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        data = json.loads(text[start : end + 1])
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def build_events(text: str) -> list[Event]:
    today = datetime.now(TZ).date()
    window_end = today + timedelta(days=config.LOOKAHEAD_DAYS)

    events: list[Event] = []
    for item in _parse_json(text or ""):
        url = (item.get("url") or "").strip()
        if not url:
            continue
        try:
            day = datetime.strptime(item["date"], "%Y-%m-%d").date()
        except (KeyError, ValueError, TypeError):
            continue
        if not today <= day <= window_end:
            continue

        start_time = item.get("start_time")
        try:
            if start_time:
                start = local_dt(f"{item['date']} {start_time}", "%Y-%m-%d %H:%M")
                end = (
                    local_dt(f"{item['date']} {item['end_time']}", "%Y-%m-%d %H:%M")
                    if item.get("end_time")
                    else None
                )
                all_day = False
            else:
                start = local_dt(f"{item['date']} 00:00", "%Y-%m-%d %H:%M")
                end = start
                all_day = True
        except ValueError:
            continue

        events.append(
            Event(
                source="parks",
                uid=url,
                title=(item.get("title") or "").strip(),
                start=start,
                end=end,
                all_day=all_day,
                url=url,
                location=(item.get("location") or "").strip(),
                description=(item.get("description") or "").strip(),
            )
        )
    return events
