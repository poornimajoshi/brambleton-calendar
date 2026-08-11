"""Parks source via Google Gemini with Google Search grounding (free tier).

Skipped if GEMINI_API_KEY is unset.
"""

import logging
import os

import config
from models import Event
from sources import parks_llm


def fetch() -> list[Event]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logging.info("parks_gemini: GEMINI_API_KEY not set, skipping")
        return []

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=config.GEMINI_MODEL,
        contents=parks_llm.prompt(),
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        ),
    )
    return parks_llm.build_events(resp.text or "")
