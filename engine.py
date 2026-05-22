import anthropic
import os
import re

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

SYSTEM_PROMPT = "You are a helpful AI assistant. Answer questions clearly and completely."


def chat(
    user_input: str,
    conversation_history: list[dict],
) -> tuple[str, list[dict]]:
    """Send a message and return (response, updated_history)."""
    working_history = conversation_history + [{"role": "user", "content": user_input}]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=working_history,
    )
    reply = response.content[0].text.strip()
    updated_history = working_history + [{"role": "assistant", "content": reply}]
    return reply, updated_history
