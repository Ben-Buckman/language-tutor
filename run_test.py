from engine import chat, check_violations
from test_cli import KNOWN_WORDS

# Preset conversation turns to test
TURNS = [
    "שלום! מה שלומך?",
    "אני רוצה לאכול לחם",
    "איפה הבית שלך?",
    "האם אתה אוהב ספרים?",
    "מה אתה עושה היום?",
]

def run():
    history = []
    print(f"Known words ({len(KNOWN_WORDS)}): {', '.join(KNOWN_WORDS)}\n")
    print("=" * 60)

    for user_input in TURNS:
        print(f"You: {user_input}")
        response, history, attempts, _ = chat(user_input, history, KNOWN_WORDS)
        attempt_note = f" (attempts: {attempts})" if attempts > 1 else ""
        print(f"AI{attempt_note}: {response}")

        # Show violation check on final response
        violations = check_violations(response, KNOWN_WORDS)
        if violations:
            print(f"  !! REMAINING VIOLATIONS: {violations}")
        else:
            print(f"  [clean]")
        print()

if __name__ == "__main__":
    run()
