from dataclasses import dataclass

from polars import LazyFrame
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

    def send_message_with_files(self, channel_id: str, file: dict):
        return self.client.files_upload_v2(
            channel=channel_id,
            file=file["file_bytes"],
            filename=file["filename"],
        )

    def generate_mentions(self, user_id_list: list[str]) -> str:
        return " ".join(f"<@{user_id}>" for user_id in user_id_list)


@dataclass
class VocabSlackBot(SlackBot):
    def generate_block_message(
        self, word: dict, usages: LazyFrame, tags: str = None
    ) -> list[dict]:
        header_content = word["word"]
        if word["word"] != word["word_full"]:
            header_content = f"{header_content}, ({word['word_full']})"
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": header_content},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"- _{word['meaning']}_"},
            },
        ]
        for sentence, translation in usages.collect().iter_rows():
            block = {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{sentence}*\n> _{translation}_"},
            }
            blocks.append(block)
        if tags:
            blocks.append(
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": tags},
                }
            )
        return blocks
