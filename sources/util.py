import html
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import config

TZ = ZoneInfo(config.TIMEZONE)

_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(text: str) -> str:
    """Turn an HTML snippet into readable plain text."""
    if not text:
        return ""
    text = text.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = _TAG_RE.sub("", text)
    return html.unescape(text).replace("\xa0", " ").strip()


def local_dt(value: str, fmt: str) -> datetime:
    """Parse a naive datetime string and attach the project timezone."""
    return datetime.strptime(value.strip(), fmt).replace(tzinfo=TZ)
