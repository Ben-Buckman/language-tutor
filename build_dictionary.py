"""
Build dictionaries/he.json from hebrew_words_full.py.
Run this once during development. Takes a while — makes many LLM calls.
Resumes from where it left off if interrupted.
"""
import os
import json
import sys

# Load .env
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

sys.stdout.reconfigure(encoding='utf-8')

from hebrew_words_full import HEBREW_WORDS
from forms_cache import _expand_words
import anthropic
import time

DICT_DIR = os.path.join(os.path.dirname(__file__), "dictionaries")
DICT_FILE = os.path.join(DICT_DIR, "he.json")


def load_dict() -> dict[str, list[str]]:
    os.makedirs(DICT_DIR, exist_ok=True)
    if os.path.exists(DICT_FILE):
        with open(DICT_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_dict(d: dict[str, list[str]]) -> None:
    os.makedirs(DICT_DIR, exist_ok=True)
    with open(DICT_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def main():
    dictionary = load_dict()
    client = anthropic.Anthropic()

    new_words = [w for w in HEBREW_WORDS if w not in dictionary]
    total = len(HEBREW_WORDS)
    cached = total - len(new_words)

    print(f"Dictionary: {total} words total, {cached} already expanded, {len(new_words)} to expand")

    if not new_words:
        print("Nothing to do — dictionary is complete.")
        return

    # Process in batches of 30 with delays to stay under rate limits
    BATCH = 30
    for i in range(0, len(new_words), BATCH):
        batch = new_words[i:i + BATCH]
        batch_num = i // BATCH + 1
        total_batches = (len(new_words) - 1) // BATCH + 1
        print(f"\nBatch {batch_num}/{total_batches}: {len(batch)} words...")

        # Retry with backoff on rate limit errors
        for attempt in range(5):
            try:
                expanded = _expand_words(batch, client, verbose=True)
                break
            except anthropic.RateLimitError:
                wait = 60 * (attempt + 1)
                print(f"  Rate limit hit, waiting {wait}s before retry...")
                time.sleep(wait)
        else:
            print("  Skipping batch after 5 failed attempts.")
            continue

        dictionary.update(expanded)
        save_dict(dictionary)
        print(f"  Saved. Dictionary now has {len(dictionary)} entries.")

        # Pause between batches to avoid hitting rate limits
        if i + BATCH < len(new_words):
            time.sleep(15)

    print(f"\nDone! he.json has {len(dictionary)} words.")


if __name__ == "__main__":
    main()
