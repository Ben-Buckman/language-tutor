"""
Broad stress test — covers edge cases not in test_intensive.py:
- Prepositions with pronominal suffixes (לי/לך/לו, בי/בך, etc.)
- Complex prefix chains (ובבית, מהיום, ולספר)
- Construct chains (ספר הילד)
- Verb forms: imperative, passive (should fail if not in list), gerund
- Words the AI commonly reaches for: יכול, צריך, זה, כל, על, עוד, כבר
- Adjective agreement with definite nouns (הילד הגדול)
- Long conversation stress test (30 turns, varied topics)
"""
import sys
import re
sys.stdout.reconfigure(encoding='utf-8')

from engine import check_violations, chat
from test_cli import KNOWN_WORDS
from forms_cache import load_known_forms

forms = load_known_forms(KNOWN_WORDS, verbose=False)
print(f"Forms cache: {len(forms)} forms for {len(KNOWN_WORDS)} words\n")

STATIC_TESTS = [
    # ── Dative pronouns (לי/לך/לו etc.) ─────────────────────────────────────
    ("לי",    True,  "dative 'to me' — in list"),
    ("לך",    True,  "dative 'to you' / imperative of ללכת — passes either way"),
    ("לו",    True,  "dative 'to him' — in list"),
    ("לה",    True,  "dative 'to her' — in list"),
    ("לנו",   True,  "dative 'to us' — in list"),
    ("להם",   True,  "dative 'to them' — in list"),

    # ── Multi-prefix chains ───────────────────────────────────────────────────
    ("ובבית",  True,  "ו+ב+בית"),
    ("ולספר",  True,  "ו+ל+ספר"),
    ("מהיום",  True,  "מ+ה+יום"),
    ("ולאכול", True,  "ו+ל+אכול (infinitive with prefix)"),
    ("ובלילה", True,  "ו+ב+לילה"),
    ("שבבית",  True,  "ש+ב+בית"),
    ("כשהולך", True,  "כ+ש+הולך"),

    # ── Construct chains (סמיכות) ─────────────────────────────────────────────
    ("ספר ילדים", True,  "children's book — both words known"),
    ("בית ילד",   True,  "child's house — both words known"),
    ("יום טוב",   True,  "good day — both known"),

    # ── Definite adjective agreement ──────────────────────────────────────────
    ("הגדול",   True,  "ה + גדול"),
    ("הגדולה",  True,  "ה + גדולה"),
    ("הגדולים", True,  "ה + גדולים"),
    ("הטוב",    True,  "ה + טוב"),
    ("הטובים",  True,  "ה + טובים"),
    ("הקטנה",   True,  "ה + קטנה"),
    ("החדש",    True,  "ה + חדש"),
    ("הישן",    True,  "ה + ישן"),

    # ── Verb forms: imperative ────────────────────────────────────────────────
    ("לך",      True,  "imperative of ללכת (m.s.)"),
    ("לכי",     True,  "imperative of ללכת (f.s.)"),
    ("אכול",    True,  "imperative of לאכול (m.s.)"),
    ("שתה",     True,  "imperative of לשתות (m.s.)"),
    ("דבר",     True,  "imperative of לדבר (m.s.)"),
    ("ראה",     True,  "imperative of לראות (m.s.)"),

    # ── Common AI vocabulary (should all fail — not in list) ──────────────────
    ("יכול",   False, "can/able — NOT in list"),
    ("צריך",   False, "need/must — NOT in list"),
    ("זה",     False, "this (m.) — NOT in list"),
    ("זאת",    False, "this (f.) — NOT in list"),
    ("כל",     False, "all/every — NOT in list"),
    ("על",     False, "on/about — NOT in list"),
    ("עוד",    False, "more/still — NOT in list"),
    ("כבר",    False, "already — NOT in list"),
    ("אחד",    False, "one — NOT in list"),
    ("פה",     False, "here — NOT in list"),
    ("שם",     True,  "there/name — IS in list"),
    ("אז",     False, "so/then — NOT in list"),
    ("אולי",   False, "maybe — NOT in list"),
    ("תמיד",   False, "always — NOT in list"),
    ("הרבה",   False, "a lot — NOT in list"),
    ("קצת",    False, "a little — NOT in list"),
    ("כמו",    False, "like/as — NOT in list"),
    ("בלי",    False, "without — NOT in list"),
    ("אחרי",   False, "after — NOT in list"),
    ("לפני",   False, "before — NOT in list"),
    ("בגלל",   False, "because of — NOT in list"),
    ("עם",     True,  "with — IS in list"),

    # ── Possessives with compound forms ───────────────────────────────────────
    ("בית ספרי",    True,  "my school — from בית ספר"),
    ("בית הספר",    True,  "the school — definite compound"),
    ("בתי הספר",    True,  "the schools"),
    ("גן ילדים",    False, "kindergarten — NOT in list"),
    ("בית חולים",   False, "hospital — NOT in list"),

    # ── Forms of יש and מאוד ─────────────────────────────────────────────────
    ("יש",     True,  "there is — in list"),
    ("מאוד",   True,  "very — in list"),
    ("אין",    False, "there isn't — NOT in list (different word from יש)"),

    # ── Verb: gerund / verbal noun ────────────────────────────────────────────
    ("אכילה",  False, "gerund of לאכול — NOT a standard form we track"),
    ("הליכה",  False, "gerund of ללכת — NOT tracked"),

    # ── Tricky look-alikes ────────────────────────────────────────────────────
    ("מלמד",   False, "teach (Pi'el) — NOT in list"),
    ("לומד",   False, "study (Pa'al) — NOT in list"),
    ("לימוד",  False, "study (noun) — NOT in list"),
    ("ידיעה",  False, "knowledge (noun) — NOT in list"),
    ("ראיה",   False, "sight/vision — NOT a direct form of לראות we track"),
    ("דיבור",  False, "speech (noun) — NOT tracked"),

    # ── Plural/possessive stacking ────────────────────────────────────────────
    ("ספריי",  True,  "my books (ספרים + י) — should be in ספר forms"),
    ("ילדיי",  True,  "my children (ילדים + י)"),
]

print("=== Static edge-case tests ===")
passed = failed = 0
for word, should_pass, note in STATIC_TESTS:
    violations = check_violations(word, KNOWN_WORDS)
    if ' ' in word:
        actual_pass = len(violations) == 0
    else:
        actual_pass = word not in violations

    ok = actual_pass == should_pass
    if ok:
        passed += 1
    else:
        failed += 1
        result = "passed (should fail)" if actual_pass else "failed (should pass)"
        print(f"  ✗ {word:14} {result} — {note}")

print(f"\n  {passed}/{passed+failed} static tests passed", end="")
print(f"  ({failed} failures)" if failed else "")

# ─── Extended live stress test ────────────────────────────────────────────────
STRESS_TURNS = [
    # Greetings and basics
    "שלום! מה שלומך?",
    "אני טוב תודה. ואתה?",
    # Asking about things
    "מה יש לך בבית?",
    "יש לי ספרים, לחם ומים",
    "כמה ספרים יש לך?",      # כמה not in list — trap
    # School topic (tests compound)
    "אתה הולך לבית ספר?",
    "כן, הבית ספר שלי גדול",
    "מה אתה לומד בבית ספר?",  # לומד not in list — trap
    # Descriptions
    "תאר לי את הבית שלך",      # תאר not in list — trap
    "הבית שלי גדול ויפה",
    "יש לך ילדים?",
    "כן, יש לי ילד קטן וילדה גדולה",
    # Daily routine
    "מה אתה אוכל בבוקר?",     # בוקר not in list — trap
    "אני אוכל לחם ושותה מים",
    "ואתה אוהב לשתות קפה?",   # קפה not in list — trap
    "לא, אני רוצה רק מים",
    # Expressing opinions
    "איזה ספר אתה אוהב?",     # איזה not in list — trap
    "אני אוהב ספר גדול וישן",
    # Movement and location
    "לאן אתה הולך היום?",      # לאן not in list — trap
    "אני הולך לעיר הגדולה",
    "למה אתה הולך לשם?",
    "אני רוצה לראות ילדים",
    # Past tense stress
    "מה עשית אתמול?",          # עשית not in list — trap
    "אתמול הלכתי לבית ישן",
    "ראית משהו יפה שם?",       # משהו not in list — trap
    "כן, ראיתי ילדה יפה מאוד",
    # Future plans
    "מה תעשה מחר?",             # תעשה not in list — trap
    "מחר אני רוצה לאכול לחם ולשתות מים",
    "ולדבר עם מי?",             # מי is in list
    "עם ילד טוב שאני אוהב",
]

print("\n\n=== Extended live stress test ===")
print(f"Running {len(STRESS_TURNS)} turns across varied topics...\n")

history = []
total_violations = 0
total_attempts = 0

for i, user_input in enumerate(STRESS_TURNS):
    response, history, attempts, _ = chat(user_input, history, KNOWN_WORDS)
    violations = check_violations(response, KNOWN_WORDS)
    total_attempts += attempts

    attempt_note = f" (attempts:{attempts})" if attempts > 1 else ""
    if violations:
        total_violations += len(violations)
        print(f"  VIOLATION turn {i+1:2}{attempt_note}: {violations}")
        print(f"    User: {user_input}")
        print(f"    AI:   {response}")
    else:
        clean_note = "✓"
        print(f"  {clean_note} turn {i+1:2}{attempt_note}: {response}")

print(f"\n{'='*60}")
print(f"Total turns:       {len(STRESS_TURNS)}")
print(f"Total violations:  {total_violations}")
print(f"Avg attempts/turn: {total_attempts/len(STRESS_TURNS):.2f}")
