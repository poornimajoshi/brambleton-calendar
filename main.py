"""Collect Brambleton kids (ages 3-5) events and sync them to Google Calendar."""

import argparse
import logging
import os

from sources import hoa, library, parks

SOURCES = [("library", library), ("hoa", hoa), ("parks", parks)]


def load_dotenv(path=".env"):
    """Load KEY=VALUE lines from a local .env into the environment, if present."""
    if not os.path.exists(path):
        return
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


def collect():
    events = []
    for name, module in SOURCES:
        try:
            found = module.fetch()
            logging.info("%s: %d events", name, len(found))
            events.extend(found)
        except Exception as exc:  # keep other sources working if one fails
            logging.error("%s failed: %s", name, exc)
    # De-duplicate by stable key.
    return list({e.key: e for e in events}.values())


def main():
    parser = argparse.ArgumentParser(description="Sync Brambleton kids events to Google Calendar.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print events without touching the calendar."
    )
    args = parser.parse_args()

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    events = sorted(collect(), key=lambda e: e.start)
    logging.info("collected %d unique events", len(events))

    if args.dry_run:
        for e in events:
            when = e.start.strftime("%a %b %d") if e.all_day else e.start.strftime("%a %b %d %I:%M%p")
            print(f"[{e.source}] {when}  {e.title}  ({e.location})")
        return

    import gcal

    created, updated = gcal.sync(events)
    logging.info("done: %d created, %d updated", created, updated)


if __name__ == "__main__":
    main()
