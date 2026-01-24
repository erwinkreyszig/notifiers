from dataclasses import dataclass
from enum import Enum
from random import randint

import polars as pl
from django.utils import timezone

from wordlist.exceptions import (
    UserDoesNotExist,
    UserDoesNotHaveLanguagePair,
    UserDoesNotHaveWordGroup,
)
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
    SERVER_ISSUE = "an unknown exception has occurred"


@dataclass
class WordGenerator:
    email: str
    language_code_from: str
    language_code_to: str
    word_group_code: str = None
    words: pl.LazyFrame = None
    word: dict = None
    user_info: dict = None

    def __post_init__(self):
        if not self.__user_exists():
            raise UserDoesNotExist()
        if not self.__user_has_language_pair():
            raise UserDoesNotHaveLanguagePair()
        if self.word_group_code and not self.__user_has_word_group_for_language():
            raise UserDoesNotHaveWordGroup()
        self.get_user_info()

    def __user_exists(self):
        return Account.objects.filter(email=self.email)

    def __user_has_language_pair(self):
        return UserLanguage.objects.filter(
            user__email=self.email,
            language_from__code=self.language_code_from,
            language_to__code=self.language_code_to,
        ).exists()

    def __user_has_word_group_for_language(self):
        return WordGroup.objects.filter(
            usergroup__user__email=self.email,
            usergroup__user__userlanguage__language_to__code=self.language_code_to,
            usergroup__group__code=self.word_group_code,
        ).exists()

    def get_words_in_language(self) -> pl.LazyFrame:
        words = Word.lazy_objects.filter(language__code=self.language_code_to).lazy
        cols = [
            COL("id").alias("word_id"),
            COL("word"),
            COL("word_full"),
            COL("meaning"),
        ]
        if self.word_group_code:
            word_groups = WordsInGroup.lazy_objects.filter(
                word__language__code=self.language_code_to,
                group__code=self.word_group_code,
            ).lazy
            words = words.join(word_groups, left_on="id", right_on="word_id")
            cols.append(COL("group_id"))
        self.words = words.select(*cols)

    def get_seen_counts(self) -> pl.LazyFrame:
        if self.words is None:
            self.get_words_in_language()
        user_words = UserWord.lazy_objects.filter(user__email=self.email).lazy
        words_with_seen_counts = self.words.join(
            user_words,
            how="left",
            on="word_id",
            join_nulls=True,
        )
        self.words = words_with_seen_counts.select(
            COL("word_id"),
            COL("word"),
            COL("meaning"),
            COL("word_full"),
            COL("seen_count").fill_null(0),
            COL("last_seen"),
        )

    def get_seen_counts_info(self) -> dict[str, int]:
        if self.words is None:
            self.get_seen_counts()
        col_name = "seen_count"
        alias = "unique_seen_counts"
        return {
            "min": self.words.select(COL(col_name).min()).collect().item(),
            "values": self.words.select(COL(col_name).unique().alias(alias))
            .collect()[alias]
            .to_list(),
        }

    def get_words_with_seen_count(self):
        if self.words is None:
            self.get_seen_counts()
        seen_counts_info = self.get_seen_counts_info()
        self.words = self.words.filter(COL("seen_count") == seen_counts_info["min"])

    def get_word_usages(self):
        if not self.word:
            self.get_word()
        return Usage.lazy_objects.filter(word__pk=self.word["word_id"]).lazy.select(
            COL("sentence"), COL("translation")
        )

    def get_word(self, random: bool = True):
        if self.words is None:
            self.get_words_with_seen_count()
        if not random:
            _words = self.words.sort(["word", "word_id"]).collect()
        else:
            _words = self.words.collect().sample(
                n=1, shuffle=True, seed=randint(0, 10000)
            )
        self.word = _words.row(0, named=True)

    def generate_word(self):
        self.get_word()
        return (self.word, self.get_word_usages())

    def log_word_usage(self):
        if not self.word:
            return False
        word = Word.objects.get(pk=self.word["word_id"])
        user = Account.objects.get(email=self.email)
        now = timezone.now()
        user_word, created = UserWord.objects.get_or_create(
            user=user, word=word, defaults={"seen_count": 1, "last_seen": now}
        )
        if not created:
            user_word.seen_count += 1
            user_word.last_seen = now
            user_word.save()
        return True

    def get_user_info(self):
        self.user_info = dict(
            Account.objects.values_list("email", "slack_id").filter(email=self.email)
        )
