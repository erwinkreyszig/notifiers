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
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Route #{route_number} as of {now_jp_tz.strftime(date_format)}",
                },
            }
        ]
        for route_name, bus_stops in locations.items():
            if len(bus_stops) == 1 and bus_stops[0] == "Not available.":
                stops_formatted = bus_stops[0]
            else:
                stops_formatted = "\n".join([f"- {stop}" for stop in bus_stops])
            route_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"> *{route_name}*",
                },
            }
            stops_block = {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": stops_formatted,
                },
            }
            blocks.extend([route_block, stops_block])
        return blocks
