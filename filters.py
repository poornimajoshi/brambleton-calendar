import holidays

import config
from models import Event

_holidays = holidays.country_holidays(config.HOLIDAYS_COUNTRY)


def _has_any(text: str, keywords: list[str]) -> bool:
    text = (text or "").lower()
    return any(k in text for k in keywords)


def is_kid_relevant(text: str) -> bool:
    """Loose family/kids relevance for feeds without age metadata."""
    return _has_any(text, config.KID_KEYWORDS)


def is_parks_relevant(text: str) -> bool:
    """A parks event must be at a park/nature venue AND be kid-oriented."""
    return _has_any(text, config.PARKS_KEYWORDS) and is_kid_relevant(text)


def is_attendable(event: Event) -> bool:
    """Keep only events attendable outside a 9-5 weekday job.

    Weekends and US public holidays are always kept (any time). On a normal
    weekday, an event is kept only if it starts before WORK_START_HOUR or at/
    after WORK_END_HOUR. All-day events are kept (they are not time-bound).
    """
    if not config.ATTENDABLE_ONLY:
        return True
    start = event.start
    if start.date() in _holidays:
        return True
    if event.all_day or start.weekday() >= 5:  # 5,6 = Sat, Sun
        return True
    hour = start.hour + start.minute / 60
    return hour < config.WORK_START_HOUR or hour >= config.WORK_END_HOUR
