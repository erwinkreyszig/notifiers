import polars as pl
from django.db import models
from simple_history.models import HistoricalRecords


class LazyQueryset(models.QuerySet):
    @property
    def lazy(self) -> pl.LazyFrame:
        return pl.LazyFrame(list(self.values()))


class Account(models.Model):
    email = models.CharField(max_length=100, unique=True, null=False, blank=False)
    slack_id = models.CharField(max_length=20, null=True, blank=True)

    objects = models.Manager()
    lazy_objects = LazyQueryset.as_manager()
    history = HistoricalRecords()

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return f"{self.email} - {self.slack_id}"


class Language(models.Model):
    code = models.CharField(max_length=5, unique=True, null=False, blank=False)
    desc = models.CharField(max_length=50, null=True, blank=True, default=None)

    objects = models.Manager()
    lazy_objects = LazyQueryset.as_manager()
    history = HistoricalRecords()

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.desc} ({self.code})"


class UserLanguage(models.Model):
    user = models.ForeignKey(Account, null=False, blank=False, on_delete=models.CASCADE)
    language_from = models.ForeignKey(
        Language,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="user_language_from",
    )
    language_to = models.ForeignKey(
        Language,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="user_language_to",
    )

    objects = models.Manager()
    lazy_objects = LazyQueryset.as_manager()
    history = HistoricalRecords()

    class Meta:
        ordering = ["user", "language_from", "language_to"]

    def __str__(self):
        return (
            f"{self.user.email}: {self.language_from.code} -> {self.language_to.code}"
        )


class LazyWordQueryset(LazyQueryset):
    def for_language(self, language_code: str) -> pl.LazyFrame:
        qs = self.filter(language__code=language_code)
        return pl.LazyFrame(list(qs.values()))


class Word(models.Model):
    language = models.ForeignKey(
        Language, null=False, blank=False, on_delete=models.CASCADE
    )
    word = models.CharField(max_length=250, null=False, blank=False)
    word_full = models.TextField(null=True, blank=True, default=None)
    meaning = models.TextField()

    objects = models.Manager()
    lazy_objects = LazyWordQueryset.as_manager()
    history = HistoricalRecords()

    class Meta:
        ordering = ["language", "word"]
        constraints = [
            models.UniqueConstraint(
                fields=["word", "word_full", "language"],
                name="word_in_language_constraint",
            )
        ]

    def __str__(self):
        return f"{self.language.code}: {self.word}"


class WordGroup(models.Model):
    code = models.CharField(max_length=100, unique=True, null=False, blank=False)
    desc = models.TextField()

    objects = models.Manager()
    lazy_objects = LazyQueryset.as_manager()
    history = HistoricalRecords()

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class LazyWIGQueryset(LazyQueryset):
    def for_word_group(self, word_group_code: str) -> pl.LazyFrame:
        qs = self.filter(group__code=word_group_code)
        return pl.LazyFrame(list(qs.values()))


class WordsInGroup(models.Model):
    group = models.ForeignKey(
        WordGroup, null=False, blank=False, on_delete=models.CASCADE
    )
    word = models.ForeignKey(Word, null=False, blank=False, on_delete=models.CASCADE)

    objects = models.Manager()
    lazy_objects = LazyWIGQueryset.as_manager()
    history = HistoricalRecords()

    class Meta:
        ordering = ["group", "word"]

    def __str__(self):
        return f"{self.group.code}: {self.word.word}"


class UserGroup(models.Model):
    user = models.ForeignKey(Account, null=False, blank=False, on_delete=models.CASCADE)
    group = models.ForeignKey(
        WordGroup, null=False, blank=False, on_delete=models.CASCADE
    )

    objects = models.Manager()
    lazy_objects = LazyQueryset.as_manager()
    history = HistoricalRecords()

    class Meta:
        ordering = ["user", "group"]

    def __str__(self):
        return f"{self.user.email}: {self.group.code}"


class LazyUsageQueryset(LazyQueryset):
    def for_language(self, language_code: str) -> pl.LazyFrame:
        qs = self.filter(word__language__code=language_code)
        return pl.LazyFrame(list(qs.values()))


class Usage(models.Model):
    word = models.ForeignKey(Word, null=False, blank=False, on_delete=models.CASCADE)
    sentence = models.TextField()
    translation = models.TextField()

    objects = models.Manager()
    lazy_objects = LazyUsageQueryset.as_manager()
    history = HistoricalRecords()

    class Meta:
        ordering = ["word"]

    def __str__(self):
        return f"{self.word.word} | {self.sentence[:10]}..."


class LazyUserWordQueryset(LazyQueryset):
    def for_language_and_user(
        self, language_code: str, email: str = None
    ) -> pl.LazyFrame:
        qs = self.filter(word__language__code=language_code)
        if email:
            qs = qs.filter(user__email=email)
        return pl.LazyFrame(list(qs.values()))


class UserWord(models.Model):
    user = models.ForeignKey(Account, null=False, blank=False, on_delete=models.CASCADE)
    word = models.ForeignKey(Word, null=False, blank=False, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(auto_now_add=True)
    seen_count = models.IntegerField(null=True, blank=True, default=0)

    objects = models.Manager()
    lazy_objects = LazyUserWordQueryset.as_manager()
    history = HistoricalRecords()

    class Meta:
        ordering = ["user", "word"]

    def __str__(self):
        return f"{self.user.email}: {self.word.word} ({self.seen_count})"
