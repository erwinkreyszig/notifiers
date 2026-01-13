from django.contrib import admin

from .models import (
    Account,
    Language,
    Usage,
    UserGroup,
    UserLanguage,
    UserWord,
    Word,
    WordGroup,
    WordsInGroup,
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    fields = ["email", "slack_id"]


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    fields = ["code", "desc"]


@admin.register(UserLanguage)
class UserLanguageAdmin(admin.ModelAdmin):
    fields = ["user", "language_from", "language_to"]


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    fields = ["language", "word", "meaning"]


@admin.register(WordGroup)
class WordGroupAdmin(admin.ModelAdmin):
    fields = ["code", "desc"]


@admin.register(WordsInGroup)
class WordsInGroupAdmin(admin.ModelAdmin):
    fields = ["group", "word"]


@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    fields = ["user", "group"]


@admin.register(Usage)
class UsageAdmin(admin.ModelAdmin):
    fields = ["word", "sentence", "translation"]


@admin.register(UserWord)
class UserWordAdmin(admin.ModelAdmin):
    fields = ["user", "word", "last_seen", "seen_count"]
