from datetime import datetime, timezone
from random import randint

import polars as pl


def create_list_of_dicts(keys, values_list):
    output = []
    for elem in values_list:
        output.append(dict(zip(keys, elem)))
    return output


def create_df(list_of_dict, lazy=True):
    df = pl.from_dicts(list_of_dict)
    if lazy:
        return df.lazy()
    return df


language_keys = ("pk", "code", "desc")
language_values = (
    (1, "EN", "English"),
    (2, "DE", "German"),
    (3, "JA", "Japanese"),
)
languages = create_list_of_dicts(language_keys, language_values)

account_keys = ("pk", "email", "slack_id")
account_values = (
    (1, "user1@email.com", "user1slack"),
    (2, "user2@email.com", "user2slack"),
)
accounts = create_list_of_dicts(account_keys, account_values)

user_language_keys = ("pk", "user", "language_from", "language_to")
user_language_values = (
    (1, 1, 1, 2),
    (2, 1, 1, 3),
    (3, 2, 1, 2),
)
user_languages = create_list_of_dicts(user_language_keys, user_language_values)

word_keys = ("pk", "language", "word", "meaning")
word_values = (
    (1, 2, "blau", "blue"),
    (2, 2, "rot", "red"),
    (3, 2, "klein", "small"),
    (4, 3, "ao", "blue"),
    (5, 3, "chiisai", "small"),
)
words = create_list_of_dicts(word_keys, word_values)

word_group_keys = ("pk", "code", "desc")
word_group_values = (
    (1, "DE_A1", "German A1"),
    (2, "DE_A2", "German A2"),
    (3, "JA_N5", "Japanese N5"),
)
word_groups = create_list_of_dicts(word_group_keys, word_group_values)

words_in_group_keys = ("pk", "group", "word")
words_in_group_values = (
    (1, 1, 1),
    (2, 1, 2),
    (3, 1, 3),
    (4, 2, 1),
    (5, 2, 2),
    (6, 3, 4),
    (7, 3, 5),
)
words_in_groups = create_list_of_dicts(words_in_group_keys, words_in_group_values)

user_group_keys = ("pk", "user", "group")
user_group_values = (
    (1, 1, 1),
    (2, 1, 2),
    (3, 1, 3),
    (4, 2, 2),
)
user_groups = create_list_of_dicts(user_group_keys, user_group_values)

usage_keys = ("pk", "word", "sentence", "translation")
usage_values = (
    (1, 1, "Das ist blau.", "This is blue."),
    (2, 1, "Es is nicht blau.", "It is not blue"),
    (3, 3, "Ich bin klein.", "I am small."),
    (4, 4, "Sore ha ao.", "That is blue."),
)
usages = create_list_of_dicts(usage_keys, usage_values)

user_word_keys = ("pk", "user", "word", "last_seen", "seen_count")
user_word_values = ((1, 1, 1, datetime.now(timezone.utc), 1),)
user_words = create_list_of_dicts(user_word_keys, user_word_values)

lazy = True
languages_df = create_df(languages, lazy=lazy)
accounts_df = create_df(accounts, lazy=lazy)
user_languages_df = create_df(user_languages, lazy=lazy)
words_df = create_df(words, lazy=lazy)
word_groups_df = create_df(word_groups, lazy=lazy)
words_in_groups_df = create_df(words_in_groups, lazy=lazy)
user_groups_df = create_df(user_groups, lazy=lazy)
usages_df = create_df(usages, lazy=lazy)
user_words_df = create_df(user_words, lazy=lazy)

email = "user1@email.com"
language_to = "DE"
word_group = "DE_A1"

# join user's language and filter selected language code(s)
resulting = (
    accounts_df.filter(pl.col("email") == email)
    .join(user_languages_df, left_on="pk", right_on="user")
    .select(
        # pl.col("email"),
        pl.col("slack_id"),
        # pl.col("language_from"),
        pl.col("language_to"),
        pl.col("pk").alias("user_pk"),
    )
)
# join language objs to get words
resulting = (
    resulting.join(languages_df, left_on="language_to", right_on="pk")
    .filter(pl.col("code") == language_to)
    .select(
        # pl.col("email"),
        pl.col("slack_id"),
        # pl.col("desc").alias("lang_desc"),
        pl.col("language_to").alias("language_pk"),
        pl.col("user_pk"),
    )
)
# join words in selected language(s)
resulting = resulting.join(words_df, left_on="language_pk", right_on="language").select(
    # pl.col("email"),
    pl.col("slack_id"),
    # pl.col("lang_desc"),
    pl.col("word"),
    pl.col("meaning"),
    pl.col("pk").alias("word_pk"),
    pl.col("user_pk"),
)
# join words in groups and word groups
resulting = (
    resulting.join(words_in_groups_df, left_on="word_pk", right_on="word")
    .join(word_groups_df, left_on="group", right_on="pk")
    .filter(pl.col("code") == word_group)
    .select(
        # pl.col("email"),
        pl.col("slack_id"),
        # pl.col("lang_desc"),
        pl.col("word"),
        pl.col("meaning"),
        # pl.col("desc").alias("group_desc"),
        pl.col("word_pk"),
        pl.col("user_pk"),
    )
)
# join usages
resulting = (
    resulting.join(usages_df, left_on="word_pk", right_on="word")
    .group_by("slack_id", "user_pk", "word_pk", "word", "meaning")
    .agg(
        pl.col("sentence").alias("sentences"),
        pl.col("translation").alias("translations"),
    )
    .select(
        pl.col("slack_id"),
        pl.col("word"),
        pl.col("meaning"),
        pl.col("sentences"),
        pl.col("translations"),
        pl.col("word_pk"),
        pl.col("user_pk"),
    )
)
# join user's seen words
resulting = resulting.join(
    user_words_df,
    left_on=["word_pk", "user_pk"],
    right_on=["word", "user"],
    how="left",
    join_nulls=True,
).select(
    pl.col("slack_id"),
    pl.col("word"),
    pl.col("meaning"),
    pl.col("sentences"),
    pl.col("translations"),
    pl.col("last_seen"),
    pl.col("seen_count").fill_null(0),
    pl.col("word_pk"),
    pl.col("user_pk"),
)

pick_random = True
final_df = resulting.filter(pl.col("seen_count") == 0)
if final_df.is_empty():
    pick_random = False
    final_df = resulting.sort(["seen_count", "last_seen"], descending=[False, True])

index = 0
if pick_random:
    index = randint(0, final_df.shape[0] - 1)
data = final_df.row(index, named=True)
