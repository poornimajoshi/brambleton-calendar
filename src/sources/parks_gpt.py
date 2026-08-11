"""Parks source via OpenAI web search. Skipped if OPENAI_API_KEY is unset."""

import logging
import os

import config
from models import Event
from sources import parks_llm


def fetch() -> list[Event]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logging.info("parks_gpt: OPENAI_API_KEY not set, skipping")
        return []

    from openai import OpenAI

    resp = OpenAI(api_key=api_key).responses.create(
        model=config.OPENAI_MODEL,
        tools=[{"type": "web_search"}],
        input=parks_llm.prompt(),
    )
    return parks_llm.build_events(resp.output_text or "")
