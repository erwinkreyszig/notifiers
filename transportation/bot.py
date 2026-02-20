# import asyncio  # noqa
import os
import re

# import httpx
import requests
from app.src.route_maps import BUS_NUMBER_URL_MAP
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.models.blocks import ActionsBlock, MarkdownBlock
from slack_sdk.models.blocks.basic_components import PlainTextObject
from slack_sdk.models.blocks.block_elements import ButtonElement

load_dotenv(".env")

app = App(token=os.getenv("SLACK_BOT_TOKEN"))


def generate_button_element(route_number: int, direction: str) -> ButtonElement:
    emoji_map = {
        "up": ":arrow_up:",
        "down": ":arrow_down:",
    }
    value_and_id = "_".join(list(map(str, (route_number, direction))))
    return ButtonElement(
        text=PlainTextObject(
            text=f"{route_number}: {emoji_map.get(direction, direction)}"
        ),
        value=value_and_id,
        action_id=value_and_id,
    )


def generate_route_blocks() -> ActionsBlock:
    button_elements = []
    for route_number, direction_dict in BUS_NUMBER_URL_MAP.items():
        for direction in direction_dict.keys():
            button_elements.append(generate_button_element(route_number, direction))
    block = ActionsBlock(
        block_id="route_options",
        elements=button_elements,
    )
    return block


def get_action_id_of_pressed_button(body: dict) -> str | None:
    actions = body.get("actions", None)
    if not actions:
        return None
    action = actions[0]
    return action.get("action_id", None)


def get_route_and_direction(action_id: str) -> tuple:
    route, direction = action_id.split("_", 1)
    route = int(route)
    return (route, direction)


# async def send_bus_info_request(route: int, direction: str) -> None:
#     url = f"{os.getenv('BUS_INFO_URL')}/{route}"
#     query_params = {"direction": direction}
#     async with httpx.AsyncClient() as client:
#         response = await client.get(url, params=query_params)


def send_bus_info_request(route: int, direction: str) -> None:
    url = f"{os.getenv('BUS_INFO_URL')}/{route}"
    query_params = {"direction": direction}
    requests.get(url=url, params=query_params)


@app.message("hamabus")
def show_route_options(message, say):
    route_blocks = generate_route_blocks()
    greeting = f"Hello <@{message['user']}>, please select a route:"
    say(
        blocks=[
            MarkdownBlock(text=greeting),
            route_blocks,
        ],
        text=greeting,
    )


@app.action(re.compile("^\d{1,3}_(up|down)$"))
def handle_button_press(args):
    args.ack()
    action_id = get_action_id_of_pressed_button(args.body)
    route, direction = get_route_and_direction(action_id)
    args.say("Looking up bus locations. Please wait...")
    args.logger.info(f"{route=}, {direction=}")
    # asyncio.run(send_bus_info_request(route, direction))
    send_bus_info_request(route, direction)


if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()
