import os

from gensim.models import KeyedVectors
import pymorphy3

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MODEL_PATH = os.path.join(PROJECT_ROOT, "model", "model.bin")

morph = pymorphy3.MorphAnalyzer()
model = KeyedVectors.load_word2vec_format(MODEL_PATH, binary=True)

async def normalize_word_with_pos(word):
    parsed = morph.parse(word)
    if parsed:
        lemma = parsed[0].normal_form
        pos = parsed[0].tag.POS
        if pos:
            return f"{lemma}_{pos.upper()}", pos
    return word, None

async def are_synonyms(wordl: str, wordr: str, threshold: float = 0.7) -> bool:
    wordl_normalized, posl = await normalize_word_with_pos(wordl)
    wordr_normalized, posr = await normalize_word_with_pos(wordr)

    if posl != posr:
        return False

    if wordl_normalized in model.key_to_index and wordr_normalized in model.key_to_index:
        similarity = model.similarity(wordl_normalized, wordr_normalized)
        return similarity >= threshold
    return False
