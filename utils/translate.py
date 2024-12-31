import re
from datetime import datetime

import pymorphy3
from googletrans import Translator

morph = pymorphy3.MorphAnalyzer()
translator = Translator()


async def translate_text(text: str, base_words: list[str]) -> str:
    start_time = datetime.now()

    # Split text into words, punctuation, and spaces (preserving original formatting)
    tokens = re.findall(r'\S+|\s+|[^\w\s]', text)

    async def process_token(token: str) -> str:
        cleaned_token = re.sub(r'[^a-zA-Zа-яА-Я]', '', token)
        if cleaned_token.isalpha():
            base_form = morph.parse(cleaned_token.lower())[0].normal_form
            if base_form in [word.lower() for word in base_words]:
                translated_word = (await translator.translate(token, src='ru', dest='en')).text
                return f"<b>{translated_word}</b>"
                # if token.isupper():
                #     return translated_word.upper()
                # elif token.istitle():
                #     return translated_word.capitalize()
                # else:
                #     return translated_word.lower()

        return token

    translated_tokens = [await process_token(token) for token in tokens]
    translated_text = ''.join(translated_tokens)

    print(f'Fragment translated in {datetime.now() - start_time}')
    return translated_text
