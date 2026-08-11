from dataclasses import dataclass
from datetime import datetime


@dataclass
class Event:
    source: str          # "library" | "hoa" | "parks"
    uid: str             # stable id within the source
    title: str
    start: datetime      # timezone-aware
    end: datetime | None
    all_day: bool
    url: str = ""
    location: str = ""
    description: str = ""

    @property
    def key(self) -> str:
        """Stable key used to de-duplicate against existing calendar events."""
        return f"{self.source}:{self.uid}"
