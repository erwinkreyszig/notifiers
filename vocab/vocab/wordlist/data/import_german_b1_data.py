import polars as pl
from django.db import transaction
from wordlist.models import Language, Usage, Word, WordGroup, WordsInGroup

FILE_PATH = "wordlist/data/B1_vocab_input.csv"


def process_row(row, language, word_group):
    word = row.get("german", None)
    word_full = row.get("german_full", None)
    meaning = row.get("english", None)
    if not word or not meaning:
        return False
    word_obj = Word.objects.create(
        language=language, word=word, word_full=word_full, meaning=meaning
    )
    _ = WordsInGroup.objects.create(group=word_group, word=word_obj)
    usages = []
    for i in range(1, 11):
        sentence_key = f"s{i}"
        translation_key = f"t{i}"
        this_sentence = row.get(sentence_key, None)
        this_translation = row.get(translation_key, None)
        if not this_sentence or not this_translation:
            break
        usages.append(
            Usage(word=word_obj, sentence=this_sentence, translation=this_translation)
        )
    Usage.objects.bulk_create(usages)
    return True


df = pl.read_csv(FILE_PATH)

lang_de, _ = Language.objects.get_or_create(code="DE", defaults={"desc": "German"})
word_group, _ = WordGroup.objects.get_or_create(
    code="DE_B1", defaults={"desc": "Goethe B1 Word list"}
)

with transaction.atomic():
    for row in df.iter_rows(named=True):
        # with transaction.atomic():
        result = process_row(row, lang_de, word_group)
        print(f"{'NOT' if not result else ''} created row for {row.get('german', '-')}")
        if not result:
            raise Exception(f"errored at {row}")
