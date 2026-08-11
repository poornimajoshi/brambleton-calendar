"""Sync events into Google Calendar via a service account (idempotent)."""

import json
import os
from datetime import timedelta

from google.oauth2 import service_account
from googleapiclient.discovery import build

import config
from models import Event

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _credentials():
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw:
        return service_account.Credentials.from_service_account_info(
            json.loads(raw), scopes=SCOPES
        )
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if path:
        return service_account.Credentials.from_service_account_file(path, scopes=SCOPES)
    raise RuntimeError(
        "Set GOOGLE_SERVICE_ACCOUNT_JSON (CI) or GOOGLE_APPLICATION_CREDENTIALS (local)."
    )


def _service():
    return build("calendar", "v3", credentials=_credentials(), cache_discovery=False)


def _body(ev: Event) -> dict:
    summary = f"{config.TITLE_PREFIX.get(ev.source, '')}{ev.title}"
    description = "\n\n".join(p for p in (ev.description, ev.url) if p)
    body = {
        "summary": summary,
        "location": ev.location,
        "description": description,
        "extendedProperties": {
            "private": {"brambletonKey": ev.key, "source": ev.source}
        },
    }
    if ev.all_day:
        end_date = (ev.end or ev.start).date()
        body["start"] = {"date": ev.start.date().isoformat()}
        # Google treats the all-day end date as exclusive.
        body["end"] = {"date": (end_date + timedelta(days=1)).isoformat()}
    else:
        end = ev.end or ev.start + timedelta(hours=1)
        body["start"] = {"dateTime": ev.start.isoformat(), "timeZone": config.TIMEZONE}
        body["end"] = {"dateTime": end.isoformat(), "timeZone": config.TIMEZONE}
    return body


def sync(events: list[Event]) -> tuple[int, int]:
    """Insert new events and update existing ones. Returns (created, updated)."""
    service = _service()
    calendar_id = os.environ["GOOGLE_CALENDAR_ID"]

    created = updated = 0
    for ev in events:
        existing = (
            service.events()
            .list(
                calendarId=calendar_id,
                privateExtendedProperty=f"brambletonKey={ev.key}",
                showDeleted=False,
                singleEvents=True,
                maxResults=1,
            )
            .execute()
            .get("items", [])
        )
        body = _body(ev)
        if existing:
            service.events().update(
                calendarId=calendar_id, eventId=existing[0]["id"], body=body
            ).execute()
            updated += 1
        else:
            service.events().insert(calendarId=calendar_id, body=body).execute()
            created += 1
    return created, updated
