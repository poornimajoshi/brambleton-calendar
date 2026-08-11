"""Sync events into Google Calendar via a service account (idempotent)."""

import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from google.oauth2 import service_account
from googleapiclient.discovery import build

import config
from models import Event

SCOPES = ["https://www.googleapis.com/auth/calendar"]
MANAGED_TAG = "brambleton"
SOURCES = ("library", "hoa", "parks")


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
            "private": {
                "brambletonKey": ev.key,
                "source": ev.source,
                "managedBy": MANAGED_TAG,
            }
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


def _managed_events(service, calendar_id, include_past: bool) -> dict[str, dict]:
    """Events previously created by this tool, keyed by event id.

    Queried per source so legacy events (tagged before managedBy existed) are
    also included. When include_past is False, only future events are returned.
    """
    time_min = None if include_past else datetime.now(ZoneInfo(config.TIMEZONE)).isoformat()
    found: dict[str, dict] = {}
    for source in SOURCES:
        page_token = None
        while True:
            resp = (
                service.events()
                .list(
                    calendarId=calendar_id,
                    privateExtendedProperty=f"source={source}",
                    timeMin=time_min,
                    showDeleted=False,
                    singleEvents=True,
                    maxResults=250,
                    pageToken=page_token,
                )
                .execute()
            )
            for item in resp.get("items", []):
                found[item["id"]] = item
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    return found


def sync(events: list[Event], prune_past: bool = False) -> tuple[int, int, int]:
    """Upsert current events and prune ones that no longer qualify.

    By default only future events are pruned; pass prune_past=True to also
    remove stale past events left by earlier runs. Returns (created, updated,
    deleted).
    """
    service = _service()
    calendar_id = os.environ["GOOGLE_CALENDAR_ID"]

    created = updated = deleted = 0
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

    # Prune future managed events that are no longer in the current set
    # (e.g. filtered out, cancelled, or removed from the source).
    current_keys = {ev.key for ev in events}
    for item in _managed_events(service, calendar_id, include_past=prune_past).values():
        key = item.get("extendedProperties", {}).get("private", {}).get("brambletonKey")
        if key not in current_keys:
            service.events().delete(calendarId=calendar_id, eventId=item["id"]).execute()
            deleted += 1

    return created, updated, deleted
