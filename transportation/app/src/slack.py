from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from slack_sdk import WebClient


@dataclass
class SlackBot:
    token: str = None
    client: WebClient = None

    def __post_init__(self):
        self.client = WebClient(token=self.token)
        self.token = None

    def send_message(
        self, channel_id: str, message: str, blocks: list[dict] | None = None
    ):
        args = {"channel": channel_id, "text": message}
        if blocks:
            args["blocks"] = blocks
        return self.client.chat_postMessage(**args)

    def generate_mentions(self, user_id_list: list[str]) -> str:
        return " ".join(f"<@{user_id}>" for user_id in user_id_list)


@dataclass
class BusConciergeSlackBot(SlackBot):
    def generate_slack_message(self, route_number: str, locations: dict) -> str:
        now_jp_tz = datetime.now(ZoneInfo("Asia/Tokyo"))
        date_format = "%d-%b-%Y %I:%M %p"
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":oncoming_bus: Route *{route_number}* as of *{now_jp_tz.strftime(date_format)}*",
                },
            }
        ]
        for destination, bus_stops in locations.items():
            stops_formatted = "\n".join([f"- {stop}" for stop in bus_stops])
            destination_block = {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f":triangular_flag_on_post: {destination}",
                    "emoji": True,
                },
            }
            stops_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": stops_formatted,
                },
            }
            blocks.extend([destination_block, stops_block])
        return blocks
