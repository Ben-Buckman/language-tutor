"""
Intensive violation checker test.
1. Static tests: known good forms and known violations
2. Live AI stress test: many conversation turns, flag any violations that slip through
"""
import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

from engine import check_violations, chat
from test_cli import KNOWN_WORDS
from forms_cache import load_known_forms

forms = load_known_forms(KNOWN_WORDS, verbose=False)
print(f"Forms cache: {len(forms)} forms for {len(KNOWN_WORDS)} words\n")

# ─── 1. Static form tests ───────────────────────────────────────────────────
# (word, should_pass, note)
STATIC_TESTS = [
    # Verb: לרצות
    ("רוצה",   True,  "לרצות present m.s."),
    ("רוצה",   True,  "לרצות present f.s."),
    ("רוצים",  True,  "לרצות present m.p."),
    ("רוצות",  True,  "לרצות present f.p."),
    ("רצה",    True,  "לרצות past 3m.s."),
    ("רצתה",   True,  "לרצות past 3f.s."),
    ("רציתי",  True,  "לרצות past 1s."),
    ("רצינו",  True,  "לרצות past 1p."),
    ("ירצה",   True,  "לרצות future 3m.s."),
    ("תרצה",   True,  "לרצות future 2m.s./3f.s."),
    ("תרצי",   True,  "לרצות future 2f.s."),
    # Verb: ללכת
    ("הולך",   True,  "ללכת present m.s."),
    ("הולכת",  True,  "ללכת present f.s."),
    ("הולכים", True,  "ללכת present m.p."),
    ("הלך",    True,  "ללכת past 3m.s."),
    ("הלכה",   True,  "ללכת past 3f.s."),
    ("הלכתי",  True,  "ללכת past 1s."),
    ("ילך",    True,  "ללכת future 3m.s."),
    ("תלכי",   True,  "ללכת future 2f.s."),
    # Verb: לאכול
    ("אוכל",   True,  "לאכול present m.s."),
    ("אוכלת",  True,  "לאכול present f.s."),
    ("אכל",    True,  "לאכול past 3m.s."),
    ("אכלתי",  True,  "לאכול past 1s."),
    ("יאכל",   True,  "לאכול future 3m.s."),
    # Verb: לדבר
    ("מדבר",   True,  "לדבר present m.s."),
    ("מדברת",  True,  "לדבר present f.s."),
    ("מדברים", True,  "לדבר present m.p."),
    ("דיברתי", True,  "לדבר past 1s."),
    ("ידבר",   True,  "לדבר future 3m.s."),
    # Verb: לראות
    ("רואה",   True,  "לראות present m.s."),
    ("רואים",  True,  "לראות present m.p."),
    ("ראיתי",  True,  "לראות past 1s."),
    ("יראה",   True,  "לראות future 3m.s."),
    # Verb: לאהוב
    ("אוהב",   True,  "לאהוב present m.s."),
    ("אוהבת",  True,  "לאהוב present f.s."),
    ("אהבתי",  True,  "לאהוב past 1s."),
    # Verb: לדעת
    ("יודע",   True,  "לדעת present m.s."),
    ("יודעת",  True,  "לדעת present f.s."),
    ("ידעתי",  True,  "לדעת past 1s."),
    # Verb: לשתות
    ("שותה",   True,  "לשתות present m.s."),
    ("שותים",  True,  "לשתות present m.p."),
    ("שתיתי",  True,  "לשתות past 1s."),
    ("ישתה",   True,  "לשתות future 3m.s."),
    # Verb: להיות
    ("הייתי",  True,  "להיות past 1s."),
    ("היה",    True,  "להיות past 3m.s."),
    ("היתה",   True,  "להיות past 3f.s."),
    ("יהיה",   True,  "להיות future 3m.s."),
    # Nouns with prefixes
    ("הבית",   True,  "ה + בית"),
    ("לבית",   True,  "ל + בית"),
    ("בבית",   True,  "ב + בית"),
    ("מהבית",  True,  "מ+ה + בית"),
    ("הספר",   True,  "ה + ספר"),
    ("בספר",   True,  "ב + ספר"),
    ("היום",   True,  "already in list"),
    ("ביום",   True,  "ב + יום"),
    ("מהיום",  True,  "מ+ה + יום"),
    # Nouns with possessives
    ("ביתי",   True,  "בית + י (my house)"),
    ("ביתך",   True,  "בית + ך (your house)"),
    ("ביתו",   True,  "בית + ו (his house)"),
    ("ביתה",   True,  "בית + ה (her house)"),
    ("ביתנו",  True,  "בית + נו (our house)"),
    ("ספרי",   True,  "ספר + י (my book)"),
    ("ילדי",   True,  "ילד + י (my child)"),
    # Adjectives
    ("גדולה",  True,  "גדול f.s."),
    ("גדולים", True,  "גדול m.p."),
    ("גדולות", True,  "גדול f.p."),
    ("טובה",   True,  "טוב f.s."),
    ("טובים",  True,  "טוב m.p."),
    ("קטנה",   True,  "קטן f.s."),
    ("יפה",    True,  "יפה (already base)"),
    ("יפים",   True,  "יפה m.p."),
    ("חדשה",   True,  "חדש f.s."),
    ("ישנה",   True,  "ישן f.s."),
    # Definite adjectives with noun
    ("הגדול",  True,  "ה + גדול"),
    ("הטובה",  True,  "ה + טובה"),
    # ─── Expected violations ──────────────────────────────────────────────
    ("מורה",   False, "teacher — NOT in list"),
    ("חבר",    False, "friend — NOT in list"),
    ("מלמד",   False, "teach (Pi'el) — different binyan from ללמוד (not in list)"),
    ("עכשיו",  True,  "already in list"),
    ("משפחה",  False, "family — NOT in list"),
    ("אמא",    False, "mother — NOT in list"),
    ("בית ספר", True, "compound in list — both tokens valid"),
    ("בתי ספר", True, "compound plural — should pass"),
    ("בית הספר", True, "compound definite — should pass"),
    ("גן ילדים", False, "compound NOT in list"),
    ("ביתי",   True,  "ביתי = my house — possessive of בית"),
    ("ביתו",   True,  "ביתו = his house — possessive of בית"),
    ("הלכנו",  True,  "ללכת past 1p."),
    ("ילדים",  True,  "ילד plural"),
    ("ילדות",  True,  "ילדה plural / ילד f.p."),
    ("ערים",   True,  "עיר plural"),
]

print("=== Static form tests ===")
passed = failed = 0
for word, should_pass, note in STATIC_TESTS:
    if " " in word:
        # multi-word: check each Hebrew token
        tokens = re.findall(r'[\u05D0-\u05EA]+', word)
        violations = check_violations(word, KNOWN_WORDS)
        actual_pass = len(violations) == 0
    else:
        violations = check_violations(word, KNOWN_WORDS)
        actual_pass = word not in violations

    ok = actual_pass == should_pass
    status = "✓" if ok else "✗"
    if ok:
        passed += 1
    else:
        failed += 1
        result = "passed (should fail)" if actual_pass else "failed (should pass)"
        print(f"  {status} {word:12} {result} — {note}")

print(f"\n  {passed}/{passed+failed} static tests passed", end="")
if failed:
    print(f"  ({failed} failures)")
else:
    print()

# ─── 2. Live AI stress test ──────────────────────────────────────────────────
STRESS_TURNS = [
    "שלום! מה שלומך היום?",
    "אני רוצה ללכת לעיר הגדולה",
    "האם יש לך ספרים טובים?",
    "מה אתה אוכל בבוקר?",
    "אני אוהב לדבר עם ילדים",
    "איפה הבית שלך? הוא גדול?",
    "אתה יודע מה השם שלי?",
    "אני רוצה לשתות מים עכשיו",
    "ראית ילד קטן ביום אתמול?",
    "מה אתה רוצה לעשות מחר?",
    "דבר איתי על ספר שאתה אוהב",
    "אנחנו רוצים ללכת לבית ישן",
    "היא ילדה יפה וטובה",
    "מתי אתה הולך לישון?",
    "אני לא יודע איפה הספר שלי",
    "הם הלכו לעיר אתמול בלילה",
    "למה אתה לא אוכל לחם?",
    "כן, אני גם אוהב מים קרים",
    "אתה רוצה לראות ספר חדש?",
    "טוב מאוד! תודה רבה לך",
]

print("\n=== Live AI stress test ===")
print(f"Running {len(STRESS_TURNS)} turns...\n")

history = []
total_violations = 0
total_attempts = 0

for i, user_input in enumerate(STRESS_TURNS):
    response, history, attempts, _, _new = chat(user_input, history, KNOWN_WORDS)
    violations = check_violations(response, KNOWN_WORDS)
    total_attempts += attempts

    attempt_note = f" (attempts:{attempts})" if attempts > 1 else ""
    if violations:
        total_violations += len(violations)
        print(f"  VIOLATION turn {i+1}{attempt_note}: {violations}")
        print(f"    User: {user_input}")
        print(f"    AI:   {response}")
    else:
        print(f"  ✓ turn {i+1:2}{attempt_note}: {response}")

print(f"\n{'='*60}")
print(f"Total turns:      {len(STRESS_TURNS)}")
print(f"Total violations: {total_violations}")
print(f"Avg attempts:     {total_attempts/len(STRESS_TURNS):.2f}")
