import os
import re
import shutil
import zipfile
import asyncio
from sys import platform

import aiofiles
import xml.etree.ElementTree as ET
from datetime import datetime

from utils.config_parser import read_config

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CACHE_DIR = os.path.join(PROJECT_ROOT, '.cache')

# Global lock to prevent simultaneous access to file extraction and release
FILE_LOCK = asyncio.Lock()

file_reference_counter = {}


async def async_unzip(zip_file_path: str, fb2_file_name: str, target_path: str) -> None:
    """
    Extracts a fb2 file from the zip archive asynchronously.
    """
    def unzip():
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            if fb2_file_name not in zip_ref.namelist():
                raise FileNotFoundError(f"{fb2_file_name} not found in archive.")
            with zip_ref.open(fb2_file_name) as source_file, open(target_path, 'wb') as target_file:
                shutil.copyfileobj(source_file, target_file)

    await asyncio.to_thread(unzip)


async def get_fb2_file(zip_file_name: str, fb2_file_name: str) -> str:
    """
    Extracts the specified .fb2 file if not already extracted and increments its reference counter.
    Returns the path to the .fb2 file.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    target_path = os.path.join(CACHE_DIR, fb2_file_name)

    async with FILE_LOCK:
        if fb2_file_name in file_reference_counter:
            file_reference_counter[fb2_file_name] += 1
            print(
                f"File {fb2_file_name} is already extracted. Reference count: {file_reference_counter[fb2_file_name]}")
            return target_path

    library_dir = read_config('config.ini')['Library']['library_root']
    zip_file_path = os.path.join(library_dir, zip_file_name)
    if not os.path.isfile(zip_file_path):
        raise FileNotFoundError(f"The file {zip_file_path} does not exist.")

    await async_unzip(zip_file_path, fb2_file_name, target_path)

    async with FILE_LOCK:
        file_reference_counter[fb2_file_name] = 1
        print(f"Extracted {fb2_file_name} to {CACHE_DIR}. Reference count: 1")

    return target_path


async def release_fb2_file(fb2_file_name: str) -> None:
    """
    Decrements the reference counter for the specified .fb2 file.
    Deletes the file if the reference count reaches zero.
    """
    async with FILE_LOCK:
        if fb2_file_name not in file_reference_counter:
            print(f"File {fb2_file_name} is not being tracked.")
            return

        file_reference_counter[fb2_file_name] -= 1
        print(
            f"Decremented reference count for {fb2_file_name}. Reference count: {file_reference_counter[fb2_file_name]}")

        if file_reference_counter[fb2_file_name] == 0:
            del file_reference_counter[fb2_file_name]
            target_path = os.path.join(CACHE_DIR, fb2_file_name)

            if os.path.isfile(target_path):
                os.remove(target_path)
                print(f"File {fb2_file_name} deleted from {CACHE_DIR}.")
            else:
                print(f"File {fb2_file_name} not found in {CACHE_DIR}.")


def remove_cache():
    if os.path.exists(CACHE_DIR) and os.path.isdir(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
        print(f"{CACHE_DIR} and its contents have been deleted.")
    else:
        print(f"{CACHE_DIR} does not exist.")


async def extract_paragraphs_from_fb2(file_path):
    """Asynchronously extract paragraphs from an FB2 file."""
    enc = 'latin-1' if platform == 'linux' else 'utf-8'
    async with aiofiles.open(file_path, 'r', encoding=enc) as file:
        content = await file.read()

    tree = ET.ElementTree(ET.fromstring(content))
    root = tree.getroot()

    namespaces = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
    paragraphs = root.findall('.//fb:body//fb:p', namespaces)

    return [para.text.strip() for para in paragraphs if para.text]


async def preprocess_paragraph(paragraph, word_patterns):
    """Preprocess a single paragraph asynchronously by counting occurrences of target words."""
    counts = {word: len(re.findall(pattern, paragraph)) for word, pattern in word_patterns.items()}
    return {"text": paragraph, "length": len(paragraph), "counts": counts}


async def preprocess_paragraphs(paragraphs, words):
    """Preprocess paragraphs asynchronously."""
    word_patterns = {word: re.compile(rf'\b{word}\b', re.IGNORECASE) for word in words}

    tasks = []
    for paragraph in paragraphs:
        tasks.append(preprocess_paragraph(paragraph, word_patterns))

    return await asyncio.gather(*tasks)


async def find_best_fragment(preprocessed, words, min_length=2500, max_length=3096):
    """Find the best fragment based on word occurrences and a preference for multiple words."""
    best_fragment = []
    best_total_count = 0

    for start_idx in range(len(preprocessed)):
        fragment = []
        fragment_length = 0
        fragment_count = {word: 0 for word in words}
        words_found = set()

        for idx in range(start_idx, len(preprocessed)):
            paragraph_data = preprocessed[idx]
            if fragment_length + paragraph_data["length"] > max_length:
                break

            fragment.append(paragraph_data["text"])
            fragment_length += paragraph_data["length"]

            for word in words:
                fragment_count[word] += paragraph_data["counts"][word]
                if paragraph_data["counts"][word] > 0:
                    words_found.add(word)

        total_count = sum(fragment_count.values())
        bonus_score = len(words_found) == len(words)

        final_score = total_count + (10 if bonus_score else 0)

        if final_score > best_total_count and min_length <= fragment_length <= max_length:
            best_fragment = fragment
            best_total_count = final_score

    return "\n\n".join(best_fragment), best_total_count


async def process_fragment_search(zip_file_name: str, fb2_file_name: str, words: list) -> str:
    start_time = datetime.now()

    text_file = await get_fb2_file(zip_file_name, fb2_file_name)
    paragraphs = await extract_paragraphs_from_fb2(text_file)
    preprocessed = await preprocess_paragraphs(paragraphs, words)
    fragment, total_count = await find_best_fragment(preprocessed, words)
    await release_fb2_file(fb2_file_name)

    print(f"Best count: {total_count}")
    with open(os.path.join(CACHE_DIR, 'last.txt'), "w", encoding="utf-8") as file:
        file.write(fragment)
    print('Fragment search processed in {}'.format(datetime.now() - start_time))
    return fragment
