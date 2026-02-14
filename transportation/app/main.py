import asyncio  # noqa
import logging
import os

from fastapi import FastAPI
from src.slack import BusConciergeSlackBot
from src.concierge import BusLocator
from src.route_maps import get_route_urls

bus_app = FastAPI()

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL") or logging.INFO))
logger = logging.getLogger(__name__)


@bus_app.get("/where/{route_number}")
async def get_bus_locations(route_number: int, direction: str | None = None):
    route_urls = get_route_urls(route_number, direction=direction)
    locator = BusLocator(route_urls, logger)
    await locator.run_playwright_context()
    current_locations = locator.get_current_bus_locations()

    slack_bot = BusConciergeSlackBot(os.getenv("SLACK_BOT_TOKEN"))
    block_message = slack_bot.generate_slack_message(
        str(route_number), current_locations
    )
    slack_bot.send_message(
        channel_id=os.getenv("SLACK_CHANNEL"), message="", blocks=block_message
    )
    return {"OK": "true"}
