from engine import chat

# Beginner Hebrew word list — ~50 words
KNOWN_WORDS = [
    # Pronouns
    "אני", "אתה", "את", "הוא", "היא", "אנחנו", "אתם", "הם",
    # Core verbs (root/infinitive — variants auto-allowed)
    "לאכול", "לשתות", "ללכת", "לדבר", "לרצות", "לאהוב", "לדעת", "להיות", "לראות",
    # Nouns
    "בית", "מים", "לחם", "ספר", "יום", "לילה", "שם", "עיר", "אוכל", "ילד", "ילדה", "אדם",
    # Common function words
    "יש", "מאוד",
    # Compound words
    "בית ספר",
    # Adjectives
    "טוב", "רע", "גדול", "קטן", "יפה", "חדש", "ישן",
    # Greetings / basics
    "שלום", "כן", "לא", "תודה", "בבקשה", "סליחה",
    # Question words
    "מה", "מי", "איפה", "מתי", "למה", "איך",
    # Time
    "היום", "מחר", "אתמול", "עכשיו",
    # Connectors
    "כי", "אבל", "גם", "רק", "עם", "או",
    # Dative pronouns (יש לי = I have, לך = to you, etc.)
    "לי", "לו", "לה", "לנו", "להם",
    # Possessives
    "שלי", "שלך", "שלו", "שלה", "שלנו", "שלכם", "שלהם",
]


def main():
    history = []
    print("Hebrew Language Tutor — Vocabulary Constrained")
    print(f"Known words: {len(KNOWN_WORDS)}")
    print("Commands: 'quit' to exit, 'words' to see word list, 'reset' to clear history")
    print("Speak to the AI in Hebrew or English — it will always respond in Hebrew.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() == "quit":
            break
        if user_input.lower() == "words":
            print(f"  Known words ({len(KNOWN_WORDS)}): {', '.join(KNOWN_WORDS)}\n")
            continue
        if user_input.lower() == "reset":
            history = []
            print("  [Conversation reset]\n")
            continue

        print("  [thinking...]", end="\r")
        response, history, attempts = chat(user_input, history, KNOWN_WORDS)

        attempt_note = f" (attempts: {attempts})" if attempts > 1 else ""
        print(f"AI{attempt_note}: {response}\n")


if __name__ == "__main__":
    main()
