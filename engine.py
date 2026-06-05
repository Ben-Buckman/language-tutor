import anthropic
import os
import re
from forms_cache import lemmatize_words, check_violations_llm, detect_due_words_llm

# Load .env if present
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

client = anthropic.Anthropic()


def build_system_prompt(known_words: list[str], language: str, due_words: list[str] = None) -> str:
    word_list = ", ".join(known_words)

    review_section = ""
    if due_words:
        review_section = f"""
REVIEW PRACTICE: The following words need reinforcement. Try to naturally use 1-2 of them in your response if it fits the conversation. Don't force them awkwardly — only use them when they make sense.
Review words: {", ".join(due_words)}
"""

    return f"""You are a conversational partner who speaks only in {language}. Have a natural, friendly conversation with the user.

Your usable vocabulary is limited to these words (plus their morphological variants — conjugations, gender forms, plurals, and common grammatical affixes):
{word_list}

STRICT RULE: Use ONLY words from this list and their morphological variants. If you cannot express an idea within this vocabulary, simplify your sentence until you can. A short simple sentence beats using an unknown word.
{review_section}
Respond only in {language}."""


def _extract_words(text: str, language: str) -> list[str]:
    """Extract word tokens from text for violation checking."""
    if language.lower() == "hebrew":
        return list(dict.fromkeys(re.findall(r'[א-ת]+', text)))
    else:
        return list(dict.fromkeys(re.findall(r"[a-zA-ZÀ-ɏЀ-ӿ]+", text)))


def check_violations(text: str, known_words: list[str], language: str = "hebrew") -> list[str]:
    """Return words in text that are not morphological variants of any known word."""
    words = _extract_words(text, language)
    return check_violations_llm(words, known_words, language)


def detect_due_words_used(text: str, due_words: list[str], language: str = "hebrew") -> list[str]:
    """Return which due_words appeared in the response in any morphological form."""
    return detect_due_words_llm(text, due_words, language)


def generate_candidate(
    conversation_history: list[dict],
    system_prompt: str,
    violations: list[str] = None
) -> str:
    messages = conversation_history.copy()

    if violations:
        violation_str = ", ".join(violations)
        messages.append({
            "role": "user",
            "content": f"[Retry: the words {violation_str} are not in the approved vocabulary. Output ONLY a new response using approved words — no notes, no explanations, just the sentences.]"
        })

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system_prompt,
        messages=messages
    )
    text = response.content[0].text.strip()
    # Strip any lines that look like internal notes (e.g. "[Note: ...]")
    lines = [l for l in text.splitlines() if not re.match(r'^\s*\[', l)]
    return "\n".join(lines).strip()


def chat(
    user_input: str,
    conversation_history: list[dict],
    known_words: list[str],
    language: str = "hebrew",
    due_words: list[str] = None,
    max_retries: int = 3
) -> tuple[str, list[dict], int, list[str], list[str]]:
    """
    Returns (response, updated_history, attempts_used, due_words_seen, new_words).
    On first violation we retry once. If violations persist after the retry, we accept
    those words as new vocabulary rather than forcing an awkward rewrite.
    """
    system_prompt = build_system_prompt(known_words, language, due_words)
    working_history = conversation_history + [{"role": "user", "content": user_input}]

    violations = None
    final_response = None
    new_words = []

    for attempt in range(max_retries):
        candidate = generate_candidate(working_history, system_prompt, violations)
        found_violations = check_violations(candidate, known_words, language)

        if not found_violations:
            final_response = candidate
            attempts_used = attempt + 1
            break
        elif attempt == 0:
            violations = found_violations
            final_response = candidate
            attempts_used = attempt + 1
        else:
            new_words = list(dict.fromkeys(found_violations))
            final_response = candidate
            attempts_used = attempt + 1
            break

    due_words_seen = detect_due_words_used(final_response, due_words or [], language)
    updated_history = working_history + [{"role": "assistant", "content": final_response}]
    return final_response, updated_history, attempts_used, due_words_seen, new_words
