"""
Generate a comprehensive Hebrew word list (~2500 most common words).
Outputs: hebrew_words_full.py containing HEBREW_WORDS list.
"""
import os
import sys
import json
import anthropic
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Load .env
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

client = anthropic.Anthropic()

CATEGORIES = [
    ("pronouns, particles, prepositions, conjunctions, determiners", 80),
    ("most common verbs as infinitives (ל prefix)", 300),
    ("common present-tense verb forms (בינוני)", 150),
    ("common nouns - people, family, body", 150),
    ("common nouns - places, nature, geography", 120),
    ("common nouns - time, calendar, days, months", 80),
    ("common nouns - food and drink", 80),
    ("common nouns - home, furniture, household items", 80),
    ("common nouns - clothing and accessories", 60),
    ("common nouns - work, profession, economy", 100),
    ("common nouns - health, medicine, body functions", 80),
    ("common nouns - education, school, learning", 70),
    ("common nouns - technology, media, communication", 80),
    ("common nouns - transport, travel, vehicles", 70),
    ("common nouns - emotions, feelings, states of mind", 80),
    ("common nouns - society, politics, law, religion", 80),
    ("common nouns - nature, animals, plants", 80),
    ("common nouns - sports, leisure, entertainment", 70),
    ("adjectives - most common", 200),
    ("adverbs - most common", 100),
    ("numbers, ordinals, quantities", 60),
    ("common phrases and expressions (multi-word)", 60),
]

def generate_category(category: str, count: int, existing: set) -> list[str]:
    existing_sample = ", ".join(list(existing)[:30]) if existing else "none yet"
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"""Generate the {count} most common/useful Hebrew words in this category: {category}

Rules:
- Return ONLY Hebrew words/phrases, no transliteration, no English
- Verbs: use infinitive form (לעשות, לאכול, etc.)
- No nikud (no vowel marks)
- No duplicates with this existing list (sample): {existing_sample}
- Include multi-word phrases only for the "phrases" category
- Return as a JSON array of strings

Respond with JSON only: {{"words": ["word1", "word2", ...]}}"""
        }]
    )

    text = response.content[0].text.strip()
    # Parse JSON
    import re
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            data = {"words": json.loads(match.group())}
        else:
            data = {"words": []}

    words = data.get("words", [])
    # Filter out duplicates and empty
    new_words = [w.strip() for w in words if w.strip() and w.strip() not in existing]
    print(f"  Got {len(new_words)} new words for: {category}")
    return new_words


def main():
    all_words = []
    seen = set()

    for category, count in CATEGORIES:
        print(f"\nGenerating: {category} ({count} words)...")
        words = generate_category(category, count, seen)
        all_words.extend(words)
        seen.update(words)
        print(f"  Total so far: {len(all_words)}")

    print(f"\nTotal words generated: {len(all_words)}")

    # Write output
    out_path = os.path.join(os.path.dirname(__file__), "hebrew_words_full.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Auto-generated: {len(all_words)} Hebrew words\n")
        f.write("HEBREW_WORDS = [\n")
        for word in all_words:
            escaped = word.replace('"', '\\"')
            f.write(f'    "{escaped}",\n')
        f.write("]\n")

    print(f"Written to hebrew_words_full.py")


if __name__ == "__main__":
    main()
