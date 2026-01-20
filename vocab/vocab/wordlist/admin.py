from django.contrib import admin
from django.db.models import F, Value
from django.db.models.functions import Coalesce, Concat

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
    fields = ("email", "slack_id")


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    fields = ("code", "desc")


@admin.register(UserLanguage)
class UserLanguageAdmin(admin.ModelAdmin):
    fields = ("user", "language_from", "language_to")
    list_display = ("user_info", "from_language", "to_language")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            user_info=Concat("user__email", Value(" / "), "user__slack_id"),
            from_language=F("language_from__desc"),
            to_language=F("language_to__desc"),
        )

    def user_info(self, obj):
        return obj.user_info

    def from_language(self, obj):
        return obj.from_language

    def to_language(self, obj):
        return obj.to_language


@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    fields = ("language", "word", "meaning")
    list_display = ("language_code", "word", "meaning")
    list_display_links = ("word",)
    ordering = ("language", "word")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(language_code=F("language__code"))

    def language_code(self, obj):
        return obj.language_code


@admin.register(WordGroup)
class WordGroupAdmin(admin.ModelAdmin):
    fields = ("code", "desc")


@admin.register(WordsInGroup)
class WordsInGroupAdmin(admin.ModelAdmin):
    fields = ("group", "word")
    list_display = ("language", "group_name", "word_simple")
    list_display_links = ("group_name", "word_simple")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            language=Coalesce("word__language__desc", "word__language__code"),
            group_info=F("group__code"),
            word_simple=F("word__word"),
        )

    def language(self, obj):
        return obj.language

    def group_name(self, obj):
        return obj.group_info

    def word_simple(self, obj):
        return obj.word_simple


@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    fields = ("user", "group")
    list_display = ("user_info", "group_info")
    list_display_links = ("user_info", "group_info")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            user_info=Concat("user__email", Value(" / "), "user__slack_id"),
            group_info=F("group__code"),
        )

    def user_info(self, obj):
        return obj.user_info

    def group_info(self, obj):
        return obj.group_info


@admin.register(Usage)
class UsageAdmin(admin.ModelAdmin):
    fields = ("word", "sentence", "translation")
    list_display = ("word_simple", "sentence", "translation")
    list_display_links = ("word_simple",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(word_simple=F("word__word"))

    def word_simple(self, obj):
        return obj.word_simple


@admin.register(UserWord)
class UserWordAdmin(admin.ModelAdmin):
    fields = ("user", "word", "last_seen", "seen_count")
    list_display = ("user_info", "word_simple", "last_seen", "seen_count")
    list_display_links = ("user_info", "word_simple")
    readonly_fields = ("last_seen",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            user_info=Concat("user__email", Value(" / "), "user__slack_id"),
            word_simple=F("word__word"),
        )

    def user_info(self, obj):
        return obj.user_info

    def word_simple(self, obj):
        return obj.word_simple
