# Brambleton Kids Calendar

Finds events for **ages 3–5** in Brambleton, VA and syncs them into a Google
Calendar. Runs automatically every day via GitHub Actions.

## Sources

| Source | Where it comes from | Filter |
| --- | --- | --- |
| **Library** | Brambleton Library (Communico events API) | Age group "Birth – Age 5" |
| **HOA** | Brambleton Community Association calendar (CivicPlus RSS) | Kid/family keywords |
| **Parks** | Loudoun County calendar (CivicPlus RSS) | Hanson/nature + kid keywords |

### Note on parks
Hal & Berni Hanson Regional Park program registrations live in **WebTrac**
(`valoudounctyweb.myvscloud.com`), which is behind Cloudflare bot protection and
cannot be scraped from an automated job. The parks source therefore reads the
county's public calendar as a best-effort fallback — it only picks up park/nature
kids events if the county publishes them there. Library programs held *at* Hanson
park still come through the **Library** source. To see the full WebTrac program
list, browse it manually: <https://www.loudoun.gov/2448/Activity-Guide>.

## How it works

Each source is scraped into a common `Event`, de-duplicated, then written to
Google Calendar. Every calendar event is tagged with a stable key
(`extendedProperties.private.brambletonKey`), so re-runs **update** existing
events instead of creating duplicates.

## Local usage

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# See what would be synced, no credentials needed:
python main.py --dry-run
```

## Google Calendar setup (service account)

1. In the [Google Cloud Console](https://console.cloud.google.com), create a
   project and enable the **Google Calendar API**.
2. Create a **Service Account** and download its **JSON key**.
3. Open Google Calendar → your target calendar → **Settings and sharing** →
   **Share with specific people** → add the service account email
   (`...@...iam.gserviceaccount.com`) with **"Make changes to events"**.
4. Copy the calendar's **Calendar ID** (Settings → "Integrate calendar").

Run it locally:

```bash
cp .env.example .env   # fill in values, or export the vars directly
export GOOGLE_CALENDAR_ID="your_calendar_id"
export GOOGLE_APPLICATION_CREDENTIALS="./service-account.json"
python main.py
```

## Scheduled runs (GitHub Actions)

Add two repository secrets (Settings → Secrets and variables → Actions):

- `GOOGLE_CALENDAR_ID` — the calendar ID.
- `GOOGLE_SERVICE_ACCOUNT_JSON` — the **entire** service-account JSON file contents.

The workflow in `.github/workflows/sync.yml` runs daily (~6am ET) and can also be
triggered manually via **Run workflow**.

## Tuning

Everything adjustable lives in `config.py`:

- `LOOKAHEAD_DAYS` — how far ahead to pull events.
- `LIBRARY_AGE_LABEL` — the library age bucket (`"Birth – Age 5"` is the finest
  the library exposes, so it also includes baby/toddler storytimes).
- `KID_KEYWORDS` / `PARKS_KEYWORDS` — relevance keywords for the HOA and parks feeds.
