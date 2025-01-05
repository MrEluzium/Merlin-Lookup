import re
from datetime import datetime

import pymorphy3
from googletrans import Translator

from utils.synonym_finder import are_synonyms

morph = pymorphy3.MorphAnalyzer()
translator = Translator()


async def translate_words_in_text(text: str, words: list[str]) -> str:
    start_time = datetime.now()
    translation_cache = {}

    # Split text into words, punctuation, and spaces (preserving original formatting)
    words_lower = [word.lower() for word in words]
    tokens = re.findall(r'\S+|\s+|[^\w\s]', text)

    async def process_token(token: str) -> str:
        cleaned_token = re.sub(r'[^a-zA-Zа-яА-ЯёЁ]', '', token)

        if not cleaned_token.isalpha():
            return token

        is_upper = cleaned_token.isupper()
        is_capitalized = cleaned_token[0].isupper() and cleaned_token[1:].islower()
        is_lower = cleaned_token.islower()

        base_form = morph.parse(cleaned_token.lower())[0].normal_form

        for word in words_lower:
            if base_form == word or await are_synonyms(base_form, word):
                if word in translation_cache:
                    translated_word = translation_cache[word]
                else:
                    translated_word = (await translator.translate(cleaned_token, src='ru', dest='en')).text
                    translation_cache[word] = translated_word
                break
        else:
            return token

        # translated_word must be lowered, except when translation changed the case.
        # We should keep translation letter case is it was changed
        if not translated_word.islower():
            if is_upper:
                translated_word = translated_word.upper()
            elif is_capitalized:
                translated_word = translated_word.capitalize()
            elif is_lower:
                translated_word = translated_word.lower()

        # Reassemble token with special characters
        reassembled_token = re.sub(r'[a-zA-Zа-яА-ЯёЁ]+', translated_word, token)
        return f"<u><b>{reassembled_token}</b></u>"

    translated_tokens = [await process_token(token) for token in tokens]
    translated_text = ''.join(translated_tokens)

    print(f'Fragment translated in {datetime.now() - start_time}')
    return translated_text
