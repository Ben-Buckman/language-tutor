from datetime import date, timedelta

# SRS intervals in days: index = number of successful exposures
INTERVALS = [1, 3, 7, 14, 30, 60, 120]


def _default_entry() -> dict:
    return {
        "exposures": 0,
        "interval": INTERVALS[0],
        "due_date": date.today().isoformat(),
        "last_seen": None,
    }


def get_due_words(known_words: list[str], word_data: dict, limit: int = 3) -> list[str]:
    """Return up to `limit` words that are due for review today."""
    today = date.today().isoformat()
    due = [w for w in known_words if word_data.get(w, _default_entry())["due_date"] <= today]
    due.sort(key=lambda w: word_data.get(w, _default_entry())["due_date"])
    return due[:limit]


def record_exposures(words: list[str], word_data: dict) -> dict:
    """Return updated word_data after recording exposures for the given words."""
    today = date.today()
    data = dict(word_data)
    for word in words:
        entry = dict(data.get(word, _default_entry()))
        entry["exposures"] += 1
        entry["last_seen"] = today.isoformat()
        next_interval = INTERVALS[min(entry["exposures"], len(INTERVALS) - 1)]
        entry["interval"] = next_interval
        entry["due_date"] = (today + timedelta(days=next_interval)).isoformat()
        data[word] = entry
    return data


def get_word_stats(known_words: list[str], word_data: dict) -> list[dict]:
    """Return SRS stats for all known words. Read-only — no side effects."""
    today = date.today().isoformat()
    result = []
    for word in known_words:
        entry = word_data.get(word, _default_entry())
        days_until_due = (date.fromisoformat(entry["due_date"]) - date.today()).days
        result.append({
            "word": word,
            "exposures": entry["exposures"],
            "interval": entry["interval"],
            "due_date": entry["due_date"],
            "last_seen": entry["last_seen"],
            "due": entry["due_date"] <= today,
            "days_until_due": max(0, days_until_due),
        })
    return result
