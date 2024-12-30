import os
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime

from utils.config_parser import read_config

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CACHE_DIR = os.path.join(PROJECT_ROOT, '.cache')
LIBRARY_DIR = read_config('config.ini')['Library']['library_root']

file_reference_counter = {}


def get_fb2_file(zip_file_name: str, fb2_file_name: str) -> str:
    """
    Extracts the specified .fb2 file if not already extracted and increments its reference counter.
    Returns the path to the .fb2 file.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)


    target_path = os.path.join(CACHE_DIR, fb2_file_name)

    if fb2_file_name in file_reference_counter:
        file_reference_counter[fb2_file_name] += 1
        print(f"File {fb2_file_name} is already extracted. Reference count: {file_reference_counter[fb2_file_name]}")
        return target_path

    zip_file_path = os.path.join(LIBRARY_DIR, zip_file_name)
    if not os.path.isfile(zip_file_path):
        raise FileNotFoundError(f"The file {zip_file_path} does not exist.")

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        fb2_files = [file for file in zip_ref.namelist() if file.endswith('.fb2')]

        if not fb2_files:
            raise FileNotFoundError("No .fb2 files found in the archive.")

        if fb2_file_name not in fb2_files:
            raise FileNotFoundError(f"The file {fb2_file_name} was not found in the archive.")

        with zip_ref.open(fb2_file_name) as source_file, open(target_path, 'wb') as target_file:
            target_file.write(source_file.read())

    file_reference_counter[fb2_file_name] = 1
    print(f"Extracted {fb2_file_name} to {CACHE_DIR}. Reference count: 1")
    return target_path


def release_fb2_file(fb2_file_name: str) -> None:
    """
    Decrements the reference counter for the specified .fb2 file.
    Deletes the file if the reference count reaches zero.
    """
    if fb2_file_name not in file_reference_counter:
        print(f"File {fb2_file_name} is not being tracked.")
        return

    file_reference_counter[fb2_file_name] -= 1
    print(f"Decremented reference count for {fb2_file_name}. Reference count: {file_reference_counter[fb2_file_name]}")

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


def extract_text_from_fb2(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    namespaces = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
    paragraphs = root.findall('.//fb:body//fb:p', namespaces)

    text = ""
    for para in paragraphs:
        text += para.text or ""
    return text


def extract_paragraphs_from_fb2(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    namespaces = {'fb': 'http://www.gribuser.ru/xml/fictionbook/2.0'}
    paragraphs = root.findall('.//fb:body//fb:p', namespaces)

    return [para.text.strip() for para in paragraphs if para.text]


def count_word_occurrences(text, word_patterns):
    return {word: len(re.findall(pattern, text)) for word, pattern in word_patterns.items()}


def preprocess_paragraphs(paragraphs, words):
    """Preprocess paragraphs by counting occurrences of target words."""
    word_patterns = {word: re.compile(rf'\b{word}\b', re.IGNORECASE) for word in words}
    preprocessed = []

    for paragraph in paragraphs:
        counts = {word: len(re.findall(pattern, paragraph)) for word, pattern in word_patterns.items()}
        preprocessed.append({"text": paragraph, "length": len(paragraph), "counts": counts})

    return preprocessed


def find_best_fragment(preprocessed, words, min_length=2500, max_length=3096):
    """Find the best fragment based on word occurrences."""
    best_fragment = []
    best_total_count = 0
    best_fragment_length = 0

    # Sliding window approach
    for start_idx in range(len(preprocessed)):
        fragment = []
        fragment_length = 0
        fragment_count = {word: 0 for word in words}

        for idx in range(start_idx, len(preprocessed)):
            paragraph_data = preprocessed[idx]
            if fragment_length + paragraph_data["length"] > max_length:
                break

            fragment.append(paragraph_data["text"])
            fragment_length += paragraph_data["length"]

            # Aggregate counts
            for word in words:
                fragment_count[word] += paragraph_data["counts"][word]

        # Check if this fragment is the best so far
        total_count = sum(fragment_count.values())
        if total_count > best_total_count and min_length <= fragment_length <= max_length:
            best_fragment = fragment
            best_total_count = total_count
            best_fragment_length = fragment_length

    return "\n\n".join(best_fragment), best_total_count


def process_fragment_search(zip_file_name: str, fb2_file_name: str, words: list) -> str:
    start_time = datetime.now()

    text_file = get_fb2_file(zip_file_name, fb2_file_name)
    paragraphs = extract_paragraphs_from_fb2(text_file)
    preprocessed = preprocess_paragraphs(paragraphs, words)
    fragment, total_count = find_best_fragment(preprocessed, words)
    release_fb2_file(fb2_file_name)

    print(f"Best count: {total_count}")
    with open(os.path.join(CACHE_DIR, 'last.txt'), "w", encoding="utf-8") as file:
        file.write(fragment)
    print('Fragment search processed in {}'.format(datetime.now() - start_time))
    return fragment
