"""
fix_dictionary.py — Re-expands words in he.json that only have 1 form.
Skips words that are genuinely single-form (particles, prepositions, etc.).
Run once: python fix_dictionary.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import json, time, os

# Load .env
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

import anthropic
from forms_cache import (
    DICT_FILE, _classify_words, _expand_verb, _expand_non_verbs,
    _is_verb, NOUN_BATCH_SIZE
)

# Words that are legitimately single-form — skip these
SKIP = {
    # Pronouns
    'אני','אתה','את','הוא','היא','אנחנו','אתם','אתן','הם','הן',
    # Prepositions / particles
    'של','ב','מ','על','עם','אל','בין','כ','עד','תחת','מעל','מתחת',
    'מול','סביב','בגלל','בשביל','במקום','בלי','חוץ','ליד','לפי',
    'לפני','אחרי','למרות','לעומת','לפחות','לפתע','לאחרונה',
    # Common adverbs / conjunctions
    'לא','כן','גם','רק','אבל','כי','אם','אז','כבר','עוד','פה',
    'כאן','שם','היום','מחר','אתמול','למה','מה','מי','איפה','מתי',
    'איך','כמה','הרבה','מעט','קצת','ממש','בערך','כמעט','בדיוק',
    'ביחד','שוב','תמיד','לפעמים','אף','עדיין','לבד','לכן','מהר',
    'לאט','בקרוב','פתאום','בדרך','בחינם','בקושי','בוודאי','מראש',
    'בהתחלה','בסוף','בעצם','כלל','בעיקרון','בערך','הנה','אולי',
    'אפשר','כנגד','בזמן','לגמרי','למעלה','למטה','לפנים','לאחור',
    # Possessives / suffixed forms
    'שלי','שלך','שלו','שלה','שלנו','שלכם','שלכן','שלהם','שלהן',
    'שלהם','שלהן','כלשהו','אחד','אחת',
    # Conjunctions
    'ו','ה','כשם','ואולם','בעוד','ואז','ולכן','בנוסף','כלומר',
    'כאשר','ברגע','ממילא',
    # Numbers / misc
    'אפס','מיליון','פי',
}


def load_dict():
    with open(DICT_FILE, encoding='utf-8') as f:
        return json.load(f)


def save_dict(d):
    with open(DICT_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f"Saved. Dictionary now has {len(d)} entries.")


def main():
    client = anthropic.Anthropic()
    d = load_dict()

    # Find all single-form words not in the skip list
    single = [k for k, v in d.items() if len(v) == 1 and k not in SKIP and ' ' not in k]
    print(f"Single-form words to re-expand: {len(single)}")

    # Split into ל-words (potential verbs) and others
    lamed_words = [w for w in single if w.startswith('ל') and len(w) > 3]
    other_words = []  # already expanded in previous run
    print(f"  Potential verbs (ל-words): {len(lamed_words)}")
    print(f"  Other words: {len(other_words)}")

    # --- Re-expand ל-words: classify first, then expand ---
    if lamed_words:
        print(f"\nClassifying {len(lamed_words)} ל-words...")
        actual_verbs = []
        non_verbs = []
        BATCH = 30
        for i in range(0, len(lamed_words), BATCH):
            batch = lamed_words[i:i+BATCH]
            try:
                classified = _classify_words(batch, client)
                # _classify_words returns {word: True/False}
                for word, is_verb in classified.items():
                    if is_verb:
                        actual_verbs.append(word)
                    else:
                        non_verbs.append(word)
            except Exception as e:
                print(f"  Classification error: {e}, treating all as non-verbs")
                non_verbs.extend(batch)
            time.sleep(3)

        print(f"  Actual verbs: {len(actual_verbs)}")
        print(f"  Non-verbs: {len(non_verbs)}")

        # Expand actual verbs
        for i, verb in enumerate(actual_verbs):
            print(f"  [verb {i+1}/{len(actual_verbs)}] {verb}")
            for attempt in range(3):
                try:
                    forms = _expand_verb(verb, client)
                    if forms and len(forms) > 1:
                        d[verb] = forms
                        print(f"    → {len(forms)} forms")
                    break
                except Exception as e:
                    wait = 60 * (attempt + 1)
                    print(f"    Error: {e}, retrying in {wait}s...")
                    time.sleep(wait)
            time.sleep(2)

        # Save after verb expansion
        save_dict(d)

        # Add non-verbs (ל-words that aren't verbs) to other_words for batch expansion
        other_words = other_words + non_verbs

    # --- Re-expand other words in batches ---
    if other_words:
        print(f"\nRe-expanding {len(other_words)} other words in batches of {NOUN_BATCH_SIZE}...")
        batches = [other_words[i:i+NOUN_BATCH_SIZE] for i in range(0, len(other_words), NOUN_BATCH_SIZE)]
        for i, batch in enumerate(batches):
            print(f"  Batch {i+1}/{len(batches)}: {', '.join(batch)}")
            for attempt in range(3):
                try:
                    expanded = _expand_non_verbs(batch, client)
                    for word, forms in expanded.items():
                        if forms and len(forms) > 1:
                            d[word] = forms
                    break
                except Exception as e:
                    wait = 60 * (attempt + 1)
                    print(f"    Error: {e}, retrying in {wait}s...")
                    time.sleep(wait)
            save_dict(d)
            time.sleep(15)

    print(f"\nDone. {sum(1 for v in d.values() if len(v) > 1)} words now have multiple forms.")


if __name__ == '__main__':
    main()
