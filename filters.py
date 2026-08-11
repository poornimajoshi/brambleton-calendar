import config


def _has_any(text: str, keywords: list[str]) -> bool:
    text = (text or "").lower()
    return any(k in text for k in keywords)


def is_kid_relevant(text: str) -> bool:
    """Loose family/kids relevance for feeds without age metadata."""
    return _has_any(text, config.KID_KEYWORDS)


def is_parks_relevant(text: str) -> bool:
    """A parks event must be at a park/nature venue AND be kid-oriented."""
    return _has_any(text, config.PARKS_KEYWORDS) and is_kid_relevant(text)
