from slack_sdk import WebClient


def get_slack_client(token):
    return WebClient(token=token)


def generate_mentions(user_id_list: list) -> str:
    return " ".join(f"<@{user_id}>" for user_id in user_id_list)


def send_slack_message(client, channel_id: str, message: str) -> None:
    return client.chat_postMessage(channel=channel_id, text=message)
