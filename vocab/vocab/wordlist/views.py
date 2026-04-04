import logging

import requests
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from wordlist.exceptions import (
    UserDoesNotExist,
    UserDoesNotHaveLanguagePair,
    UserDoesNotHaveWordGroup,
)
from wordlist.slack import VocabSlackBot
from wordlist.utils import Responses, WordGenerator

logger = logging.getLogger(__name__)


class VocabRunner(APIView):
    def post(self, request, format=None):
        this_method_name = self.post.__name__
        email = request.data.get("email", None)
        language_code_from = request.data.get("language_code_from", None)
        language_code_to = request.data.get("language_code_to", None)
        word_group_code = request.data.get("word_group_code", None)

        status_400 = status.HTTP_400_BAD_REQUEST
        if None in (email, language_code_from, language_code_to, word_group_code):
            return Response({"reason": Responses.INCOMPLETE.value}, status=status_400)
        try:
            wg = WordGenerator(
                email, language_code_from, language_code_to, word_group_code
            )
        except UserDoesNotExist:
            return Response(
                {"reason": Responses.EMAIL_DOES_NOT_EXIST.value}, status=status_400
            )
        except UserDoesNotHaveLanguagePair:
            return Response(
                {"reason": Responses.NO_LANGUAGE_PAIR.value}, status=status_400
            )
        except UserDoesNotHaveWordGroup:
            return Response(
                {"reason": Responses.NO_WORD_GROUP.value}, status=status_400
            )
        except Exception as e:
            logger.debug(
                f"{this_method_name} | exception occurred "
                f"in initializing WordGenerator class: {e}"
            )
            return Response(
                {"reason": Responses.SERVER_ISSUE.value},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            word, usages = wg.generate_word()
        except Exception as e:
            logger.debug(
                f"{this_method_name} | exception occurred in generating word: {e}"
            )
            return Response(
                {"reason": Responses.SERVER_ISSUE.value},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        audio_files = []
        if settings.NEUTTS_SERVER_URL:
            for sentence, _ in usages.collect().iter_rows():
                filename = f"{sentence[:16].replace(' ', '_')}.wav"
                try:
                    response = requests.post(
                        settings.NEUTTS_SERVER_URL, json={"text": sentence}
                    )
                    if response.status_code == 200:
                        audio_files.append(
                            {
                                "file_bytes": response.content,
                                "filename": filename,
                                "title": filename.replace(".wav", "..."),
                            }
                        )
                    else:
                        logger.info(
                            f"Failed to generate audio for sentence: {sentence}"
                        )
                except Exception as e:
                    logger.info(
                        f"Error occurred while generating audio for sentence: {sentence}, error: {e}"
                    )

        # TODO: join this to the try-except above, use specific exceptions to catch
        try:
            slack_bot = VocabSlackBot(token=settings.SLACK_BOT_TOKEN)
            tags = slack_bot.generate_mentions(list(wg.user_info.values()))
            blocks = slack_bot.generate_block_message(word, usages, tags)
            result = slack_bot.send_message(
                settings.SLACK_CHANNEL, message="", blocks=blocks
            )
        except Exception as e:
            logger.debug(
                f"{this_method_name} | exception occurred "
                f"in preparing slack message: {e}"
            )
            return Response(
                {"reason": Responses.SERVER_ISSUE.value},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if getattr(result, "status_code", None) != 200:
            logger.debug(
                f"{this_method_name} | exception occurred in sending slack message"
            )
            return Response(
                {"reason": "error in sending slack message"}, status=status_400
            )

        if not wg.log_word_usage():
            return Response(
                {"reason": Responses.SERVER_ISSUE.value},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        for audio_file in audio_files:
            try:
                slack_bot.send_message_with_files(
                    channel_id=settings.SLACK_CHANNEL, file=audio_file
                )
            except Exception as e:
                logger.info(
                    f"Failed to send audio file: {audio_file['filename']} to Slack, error: {e}"
                )
                continue

        return Response({"message": "new word sent"}, status=status.HTTP_200_OK)
