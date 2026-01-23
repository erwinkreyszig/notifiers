from slack_sdk import WebClient


def get_slack_client(token):
    return WebClient(token=token)


def generate_mentions(user_id_list: list) -> str:
    return " ".join(f"<@{user_id}>" for user_id in user_id_list)


def send_slack_message(
    client, channel_id: str, message: str, blocks: list = None
) -> None:
    args = {"channel": channel_id, "text": message}
    if blocks:
        args["blocks"] = blocks
    return client.chat_postMessage(**args)
