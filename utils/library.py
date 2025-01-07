import os
import re
import shutil
import zipfile
import asyncio
from pathlib import Path

import aiofiles
import xml.etree.ElementTree as ET
from datetime import datetime

from chardet import UniversalDetector

from utils.config_parser import read_config
from utils.database import BookSearchResult, get_book_by_url

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CACHE_DIR = os.path.join(PROJECT_ROOT, '.cache')

# Global lock to prevent simultaneous access to file extraction and release
FILE_LOCK = asyncio.Lock()

file_reference_counter = {}


async def yield_zip_file_names(folder_path: str) -> (str, str):
    """Yields file names from ZIP archives in a folder one by one."""
    folder = Path(folder_path)
    for file in folder.iterdir():
        if file.suffix == '.zip' and file.is_file():
            try:
                with zipfile.ZipFile(file, 'r') as archive:
                    for name in archive.namelist():
                        yield file.name, name
            except zipfile.BadZipFile:
                print(f"Error: {file.name} is not a valid ZIP file.")


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
    try:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            content = await file.read()
    except UnicodeDecodeError:
        print(f"{file_path} could not be read with utf-8. Encoding auto detection...")
        detector = UniversalDetector()
        for line in open(file_path, 'rb'):
            detector.feed(line)
            if detector.done: break
        detector.close()
        print(f"Auto-detected encoding for {file_path}: {detector.result['encoding']}")
        async with aiofiles.open(file_path, 'r', encoding=detector.result['encoding']) as file:
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
    word_patterns = {
        word: re.compile(rf'(?<![а-яёa-z]){word}(?![а-яёa-z])', re.IGNORECASE)
        for word in words
    }

    tasks = []
    for paragraph in paragraphs:
        tasks.append(preprocess_paragraph(paragraph, word_patterns))

    return await asyncio.gather(*tasks)


async def find_best_fragment(preprocessed, words, min_length=512, max_length=2096):
    """Find the best fragment starting from a paragraph containing target words, and cut paragraphs without specified words from start and end."""
    best_fragment = []
    best_score = -1
    best_fragment_count = {}

    for start_idx in range(len(preprocessed)):
        current_length = 0
        current_fragment = []
        current_counts = {word: 0 for word in words}

        for end_idx in range(start_idx, len(preprocessed)):
            para_data = preprocessed[end_idx]
            new_length = current_length + para_data["length"]

            if new_length > max_length:
                break

            current_length = new_length
            current_fragment.append(para_data)

            for word in words:
                current_counts[word] += para_data["counts"][word]

            if current_length >= min_length and all(current_counts[word] > 0 for word in words):
                score = sum(current_counts.values()) - (end_idx - start_idx) * 0.1

                if score > best_score:
                    best_score = score
                    best_fragment = current_fragment.copy()
                    best_fragment_count = current_counts.copy()

    if not best_fragment:
        return "", {word: 0 for word in words}

    return "\n\n".join(p["text"] for p in best_fragment), best_fragment_count


async def process_fragment_search(zip_file_name: str, fb2_file_name: str, words: list, max_length: int = 2096) -> tuple[str, dict[str, int]]:
    start_time = datetime.now()

    text_file = await get_fb2_file(zip_file_name, fb2_file_name)
    paragraphs = await extract_paragraphs_from_fb2(text_file)
    preprocessed = await preprocess_paragraphs(paragraphs, words)
    fragment, words_found = await find_best_fragment(preprocessed, words, max_length=max_length)
    await release_fb2_file(fb2_file_name)

    print('Fragment search processed in {}'.format(datetime.now() - start_time))
    return fragment, words_found


async def process_full_search(words: list, max_length: int = 2096) -> tuple[str, BookSearchResult]:
    library_dir = read_config('config.ini')['Library']['library_root']
    async for zip_name, file_name in yield_zip_file_names(library_dir):
        print(f'Processing {file_name} from {zip_name}...')
        fragment, words_found = await process_fragment_search(zip_name, file_name, words, max_length=3096)
        print(words_found)
        if len(words_found) != len(words) or any(n < 1 for n in words_found.values()):
            continue

        url = "fb2.Flibusta.Net/" + zip_name + "/" + file_name
        book = await get_book_by_url(url)
        return fragment, book
