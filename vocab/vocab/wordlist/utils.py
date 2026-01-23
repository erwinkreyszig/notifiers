from enum import Enum
from random import randint

import polars as pl
from django.utils import timezone

from wordlist.models import (
    Account,
    Usage,
    UserLanguage,
    UserWord,
    Word,
    WordGroup,
    WordsInGroup,
)

COL = pl.col


class Responses(Enum):
    INCOMPLETE = "request is missing required one or more keys: email, language_code_from, language_code_to, word_group_code"
    EMAIL_DOES_NOT_EXIST = "email is not in the system"
    NO_LANGUAGE_PAIR = "language pair for email is not in the system"
    NO_WORD_GROUP = (
        "word_group_code for email and language_code_to is not in the system"
    )
    USER_HAS_NO_LANGUAGE = "language is not registered to email"
    USER_HAS_NO_WORD_GROUP = "word group is not registered to email"


def user_exists(email: str) -> bool:
    return Account.objects.filter(email=email).exists()


def user_has_language_pair(email: str, language_from: str, language_to: str) -> bool:
    return UserLanguage.objects.filter(
        user__email=email,
        language_from__code=language_from,
        language_to__code=language_to,
    ).exists()


def user_has_group_for_language(
    email: str, language_code: str, word_group_code: str
) -> bool:
    return WordGroup.objects.filter(
        usergroup__user__email=email,
        usergroup__user__userlanguage__language_to__code=language_code,
        usergroup__group__code=word_group_code,
    ).exists()


def get_words_in_language(
    language_code: str, word_group_code: str = None
) -> pl.LazyFrame:
    words = Word.lazy_objects.filter(language__code=language_code).lazy
    cols = [
        COL("id").alias("word_id"),
        COL("word"),
        COL("word_full"),
        COL("meaning"),
    ]
    if word_group_code:
        word_groups = WordsInGroup.lazy_objects.filter(
            word__language__code=language_code, group__code=word_group_code
        ).lazy
        words = words.join(word_groups, left_on="id", right_on="word_id")
        cols.append(COL("group_id"))
    return words.select(*cols)


def attach_seen_counts(words: pl.LazyFrame, email: str) -> pl.LazyFrame:
    user_words = UserWord.lazy_objects.filter(user__email=email).lazy
    words_with_seen_counts = words.join(
        user_words,
        how="left",
        on="word_id",
        join_nulls=True,
    )
    return words_with_seen_counts.select(
        COL("word_id"),
        COL("word"),
        COL("meaning"),
        COL("word_full"),
        COL("seen_count").fill_null(0),
        COL("last_seen"),
    )


def get_seen_counts_info(words: pl.LazyFrame) -> dict[str, int]:
    col_name = "seen_count"
    alias = "unique_seen_counts"
    return {
        "min": words.select(COL(col_name).min()).collect().item(),
        "values": words.select(COL(col_name).unique().alias(alias))
        .collect()[alias]
        .to_list(),
    }


def get_words_with_seen_count(words: pl.LazyFrame, seen_count: int) -> pl.LazyFrame:
    return words.filter(COL("seen_count") == seen_count)


def get_random_word(words: pl.LazyFrame) -> dict:
    return (
        words.collect()
        .sample(n=1, shuffle=True, seed=randint(0, 10000))
        .row(0, named=True)
    )


def get_word_usages(word_id: int) -> pl.LazyFrame:
    return Usage.lazy_objects.filter(word__pk=word_id).lazy.select(
        COL("sentence"), COL("translation")
    )


def log_word_usage(word_id: int, email: str) -> None:
    word = Word.objects.get(pk=word_id)
    user = Account.objects.get(email=email)
    now = timezone.now()
    user_word, created = UserWord.objects.get_or_create(
        user=user, word=word, defaults={"seen_count": 1, "last_seen": now}
    )
    if not created:
        user_word.seen_count += 1
        user_word.last_seen = now
        user_word.save()


def get_new_word(email: str, language_code: str, word_group_code: str) -> dict:
    words = get_words_in_language(language_code, word_group_code)
    words = attach_seen_counts(words, email)
    seen_counts_info = get_seen_counts_info(words)
    words = get_words_with_seen_count(words, seen_counts_info["min"])
    return get_random_word(words)


def get_user_info(email: str) -> dict:
    account = Account.objects.values_list("email", "slack_id").filter(email=email)
    return dict(account)


def generate_slack_message(word: dict, usages: pl.LazyFrame, tags: str = None) -> str:
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
