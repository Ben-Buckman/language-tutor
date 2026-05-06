"""
One-time script: detect and re-expand incomplete noun entries for known words.

A noun/adjective entry is considered incomplete if:
  - fewer than 8 forms in static dict
  - no form contains ך (a reliable possessive/suffix marker)
  - not a verb (doesn't start with ל)
  - not an obvious particle/adverb/pronoun (excluded by PARTICLES set below)

Writes fixed entries back into dictionaries/he.json.
"""
import json, os, sys
import anthropic

sys.stdout.reconfigure(encoding='utf-8')

from forms_cache import _expand_words, _static_dict
from word_list_500 import KNOWN_WORDS_500

DICT_FILE = os.path.join(os.path.dirname(__file__), "dictionaries", "he.json")

# Clear-cut particles, pronouns, adverbs, conjunctions, prepositions that
# correctly have very few forms — do NOT re-expand these.
PARTICLES = {
    'אני', 'אתה', 'את', 'הוא', 'היא', 'אנחנו', 'אנו', 'אתם', 'אתן',
    'הם', 'הן', 'זה', 'זו', 'זאת', 'אלה', 'אלו', 'כזה', 'כזו',
    'יש', 'אין', 'כי', 'אבל', 'גם', 'רק', 'או', 'אם', 'אז', 'אחרת',
    'כבר', 'עכשיו', 'היום', 'מחר', 'אתמול', 'תמיד', 'מאוד', 'ממש',
    'כמעט', 'בדיוק', 'ביחד', 'יחד', 'כאן', 'פה', 'שם', 'שמה',
    'מה', 'מי', 'איפה', 'מתי', 'למה', 'איך', 'כמה',
    'כל', 'כלום', 'משהו', 'מישהו', 'כלשהו',
    'כן', 'לא', 'אולי', 'בוודאי', 'ודאי', 'בסדר',
    'מאוד', 'מהר', 'כבר', 'בשביל', 'בלי', 'חוץ', 'כאשר',
    'שלי', 'שלך', 'שלו', 'שלה', 'שלנו', 'שלכם', 'שלהם', 'שלהן',
    'לי', 'לו', 'לה', 'לנו', 'לכם', 'להם', 'לך',
    'ב', 'כ', 'מ', 'ו', 'ה', 'ל', 'אל', 'על', 'עד', 'עם', 'מן',
    'ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני', 'יולי',
    'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר',
    'בבקשה', 'תודה', 'סליחה', 'שלום',
    'אחד', 'אחת', 'שניים', 'שתיים', 'שלושה', 'ארבעה', 'חמישה',
    'שישה', 'שבעה', 'שמונה', 'תשעה', 'עשרה',
    'עשר', 'עשרים', 'שלושים', 'ארבעים', 'חמישים',
    'ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי',
    'היום', 'פלוס', 'מינוס', 'אמת', 'אמת',
    # present-tense adjective-verbs that don't take possessives
    'יכול', 'רואה', 'נותן', 'שואל', 'יושבת', 'שותה', 'מחכה',
    'מבין', 'מרגיש', 'אוהב', 'יודע', 'הולך', 'מדבר',
}


def is_incomplete(word: str, forms: list) -> bool:
    """Return True if word is a noun/adjective with suspiciously few forms."""
    if ' ' in word:
        return False  # compounds handled separately
    if word.startswith('ל'):
        return False  # verb infinitive
    if word in PARTICLES:
        return False
    flat = [f for f in forms if isinstance(f, str)]
    if len(flat) >= 8:
        return False
    # Must not already have ך-forms (reliable sign of complete possessive coverage)
    return not any('ך' in f for f in flat)


def run():
    known = list(dict.fromkeys(KNOWN_WORDS_500))

    incomplete = [
        w for w in known
        if w in _static_dict and is_incomplete(w, _static_dict[w])
    ]
    not_in_dict = [
        w for w in known
        if w not in _static_dict and ' ' not in w and not w.startswith('ל') and w not in PARTICLES
    ]

    print(f"Incomplete entries ({len(incomplete)}):")
    for w in incomplete:
        print(f"  {w}: {len(_static_dict[w])} forms")
    print(f"\nNot in dict: {not_in_dict}")

    to_expand = incomplete + not_in_dict
    if not to_expand:
        print("Nothing to fix.")
        return

    print(f"\nExpanding {len(to_expand)} words...")
    client = anthropic.Anthropic()
    expanded = _expand_words(to_expand, client, verbose=True)

    with open(DICT_FILE, encoding='utf-8') as f:
        d = json.load(f)

    for word, forms in expanded.items():
        d[word] = sorted(set(d.get(word, [])) | set(forms))

    with open(DICT_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

    print(f"\nDone. {len(expanded)} entries updated in he.json.")
    for w, forms in expanded.items():
        print(f"  {w}: {len(forms)} forms")


if __name__ == "__main__":
    run()
