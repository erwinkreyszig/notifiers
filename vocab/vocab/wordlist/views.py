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


class VocabRunner(APIView):
    def post(self, request, format=None):
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
        except Exception:
            return Response(
                {"reason": Responses.SERVER_ISSUE.value},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            word, usages = wg.generate_word()
        except Exception:
            return Response(
                {"reason": Responses.SERVER_ISSUE.value},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # TODO: join this to the try-except above, use specific exceptions to catch
        try:
            slack_bot = VocabSlackBot(token=settings.SLACK_BOT_TOKEN)
            tags = slack_bot.generate_mentions(list(wg.user_info.values()))
            blocks = slack_bot.generate_block_message(word, usages, tags)
            result = slack_bot.send_message(
                settings.SLACK_CHANNEL, message="", blocks=blocks
            )
        except Exception:
            return Response(
                {"reason": Responses.SERVER_ISSUE.value},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if getattr(result, "status_code", None) != 200:
            return Response(
                {"reason": "error in sending slack message"}, status=status_400
            )

        if not wg.log_word_usage():
            return Response(
                {"reason": Responses.SERVER_ISSUE.value},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"message": "new word sent"}, status=status.HTTP_200_OK)
