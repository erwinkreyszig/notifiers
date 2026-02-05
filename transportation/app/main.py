import logging
import os

from fastapi import FastAPI
from src.concierge import BusLocator
from src.route_maps import BUS_NUMBER_URL_MAP
from src.slack import BusConciergeSlackBot

bus_app = FastAPI()

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL") or logging.INFO))
logger = logging.getLogger(__name__)


@bus_app.get("/where/{route_number}")
def get_bus_locations(route_number: int):
    locator = BusLocator(BUS_NUMBER_URL_MAP[route_number], logger)
    locator.run_playwright_context()
    current_locations = locator.get_current_bus_locations()

    slack_bot = BusConciergeSlackBot(os.getenv("SLACK_BOT_TOKEN"))
    block_message = slack_bot.generate_slack_message(
        str(route_number), current_locations
    )
    slack_bot.send_message(
        channel_id=os.getenv("SLACK_CHANNEL"), message="", blocks=block_message
    )
    return {"OK": "true"}
