from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from wordlist.slack import generate_mentions, get_slack_client, send_slack_message
from wordlist.utils import (
    Responses,
    generate_slack_message,
    get_new_word,
    get_user_info,
    get_word_usages,
    user_exists,
    user_has_group_for_language,
    user_has_language_pair,
)


class VocabRunner(APIView):
    def post(self, request, format=None):
        email = request.data.get("email", None)
        language_code_from = request.data.get("language_code_from", None)
        language_code_to = request.data.get("language_code_to", None)
        word_group_code = request.data.get("word_group_code", None)

        print(f"{email=}, {language_code_from=}, {word_group_code=}")
        this_status = status.HTTP_400_BAD_REQUEST
        if None in (email, language_code_from, language_code_to, word_group_code):
            return Response({"reason": Responses.INCOMPLETE.value}, status=this_status)
        if not user_exists(email):
            return Response(
                {"reason": Responses.EMAIL_DOES_NOT_EXIST.value}, status=this_status
            )
        if not user_has_language_pair(email, language_code_from, language_code_to):
            return Response(
                {"reason": Responses.NO_LANGUAGE_PAIR.value}, status=this_status
            )
        if not user_has_group_for_language(email, language_code_to, word_group_code):
            return Response(
                {"reason": Responses.NO_WORD_GROUP.value}, status=this_status
            )

        word = get_new_word(email, language_code_to, word_group_code)
        usages = get_word_usages(word["word_id"])
        user_info = get_user_info(email)
        tags = generate_mentions(list(user_info.values()))
        slack_message = generate_slack_message(word, usages, tags=tags)
        slack_client = get_slack_client(settings.SLACK_BOT_TOKEN)
        slack_response = send_slack_message(
            slack_client,
            channel_id=settings.SLACK_CHANNEL,
            message="",
            blocks=slack_message,
        )
        if getattr(slack_response, "status_code", None) != 200:
            return Response(
                {"reason": "error in sending slack message"}, status=this_status
            )
        return Response({"message": "new word sent"}, status=status.HTTP_200_OK)
