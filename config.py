"""Central configuration: feed URLs, filters, and calendar settings."""

TIMEZONE = "America/New_York"
LOOKAHEAD_DAYS = 60

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124 Safari/537.36"
)

# --- Library (Brambleton branch, Communico backend) ---
LIBRARY_API = "https://loudoun.libnet.info/eeventcaldata"
LIBRARY_BRANCH = "Brambleton Library"
# Communico's age bucket that covers 3-5 year olds.
LIBRARY_AGE_LABEL = "Birth - Age 5"

# --- HOA (Brambleton Community Association, CivicPlus RSS) ---
HOA_RSS = "https://www.brambletonhoa.com/RSSFeed.aspx?ModID=58&CID=All-calendar.xml"

# --- Parks (Loudoun County, CivicPlus RSS) ---
# NOTE: Hal & Berni Hanson program registrations live in WebTrac, which is
# Cloudflare-protected and cannot be scraped. This county feed is best-effort:
# it captures park/nature events only if the county publishes them here.
COUNTY_RSS = "https://www.loudoun.gov/RSSFeed.aspx?ModID=58&CID=All-calendar.xml"

# Label prefixed to each event title so the source is obvious in the calendar.
TITLE_PREFIX = {
    "library": "[Library] ",
    "hoa": "[HOA] ",
    "parks": "[Parks] ",
}

# HOA/parks feeds have no age metadata, so relevance is keyword-based.
KID_KEYWORDS = [
    "kid", "child", "children", "toddler", "preschool", "tot", "baby",
    "story", "storytime", "family", "puppet", "craft", "magic", "petting",
    "egg hunt", "easter", "halloween", "trunk or treat", "trick or treat",
    "santa", "breakfast with", "movie", "touch a truck", "pumpkin",
    "ice cream", "little", "play", "sensory", "nature explorer",
]

# A parks event must mention one of these places/themes to be considered.
PARKS_KEYWORDS = [
    "hanson", "regional park", "nature center", "nature overlook",
    "splash pad", "nature explorer",
]

# --- Attendability filter ---
# Keep only events attendable outside a 9-5 weekday job: weekday events before
# WORK_START_HOUR or at/after WORK_END_HOUR, plus ALL weekend and holiday events.
ATTENDABLE_ONLY = True
WORK_START_HOUR = 9
WORK_END_HOUR = 17
HOLIDAYS_COUNTRY = "US"

# --- LLM parks source (best-effort; WebTrac is Cloudflare-blocked) ---
# Which provider to use for the web-search parks source: "gemini", "openai", or "off".
# NOTE: the *free* Gemini/OpenAI tiers do NOT include web search / grounding, so a
# usable parks source requires billing enabled on the chosen provider. Kept "off".
PARKS_PROVIDER = "off"
GEMINI_MODEL = "gemini-flash-latest"
OPENAI_MODEL = "gpt-4o"
