"""
Morphological forms lookup for vocabulary constraint engine.

Primary source: dictionaries/he.json — a pre-built static dictionary covering
~2000+ common Hebrew words with all their surface forms. Zero LLM calls for
words in the dictionary.

For runtime violation checking, the LLM directly determines whether a word
is a morphological variant of a known word — no hardcoded grammar rules.

The expansion functions (_expand_verb, _expand_non_verbs, etc.) are Hebrew-specific
and used only by build_dictionary.py / fix_dict_entries.py (build-time only).
"""
import json
import os
import re
import sys
from typing import Optional
import anthropic

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

DICT_FILE = os.path.join(os.path.dirname(__file__), "dictionaries", "he.json")
OVERFLOW_CACHE_FILE = os.path.join(os.path.dirname(__file__), "overflow_cache.json")
NOUN_BATCH_SIZE = 20

# Module-level: loaded once at import time (Hebrew static dict only)
def _load_static_dict_now() -> dict:
    if os.path.exists(DICT_FILE):
        with open(DICT_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}

_static_dict: dict = _load_static_dict_now()

# Reverse index: any surface form -> headword key in _static_dict
def _build_reverse_index(d: dict) -> dict[str, str]:
    candidates: dict[str, list[str]] = {}

    def _register(token: str, headword: str) -> None:
        if ' ' not in token:
            if token not in candidates:
                candidates[token] = []
            candidates[token].append(headword)

    for headword, forms in d.items():
        for form in forms:
            if isinstance(form, str):
                if ' ' not in form:
                    m = re.search(r'[\u05D0-\u05EA]+', form)
                    if m:
                        _register(m.group(), headword)
            elif isinstance(form, list):
                for f in form:
                    if ' ' not in f:
                        m = re.search(r'[\u05D0-\u05EA]+', f)
                        if m:
                            _register(m.group(), headword)

    def _best(token: str, headwords: list[str]) -> str:
        def score(hw: str) -> tuple:
            if hw == token:
                return (0, 0)
            return (1, abs(len(hw) - len(token)))
        return min(headwords, key=score)

    return {token: _best(token, hws) for token, hws in candidates.items()}

_reverse_index: dict[str, str] = _build_reverse_index(_static_dict)

_LOOKUP_PREFIXES = ('ו', 'ה', 'ב', 'ל', 'מ', 'כ', 'ש')


def get_prefix_variants(word: str) -> list[str]:
    """Return all prefix-stripped variants of word (BFS, no dictionary lookup)."""
    queue = [word]
    seen: set[str] = {word}
    for current in queue:
        for p in _LOOKUP_PREFIXES:
            if current.startswith(p) and len(current) - len(p) >= 2:
                stripped = current[len(p):]
                if stripped not in seen:
                    seen.add(stripped)
                    queue.append(stripped)
    return list(seen)


# ─── Per-language cache management ───────────────────────────────────────────

def _known_forms_cache_file(language: str) -> str:
    name = "known_forms_cache" if language == "hebrew" else f"known_forms_cache_{language}"
    return os.path.join(os.path.dirname(__file__), f"{name}.json")


def _lemma_cache_file(language: str) -> str:
    name = "lemma_cache" if language == "hebrew" else f"lemma_cache_{language}"
    return os.path.join(os.path.dirname(__file__), f"{name}.json")


# Per-language in-memory caches (loaded lazily)
_known_forms_cache_by_lang: dict[str, set[str]] = {}
_lemma_cache_by_lang: dict[str, dict[str, str]] = {}
# Violation cache: (word, frozenset(known_words), language) -> True
_violation_cache: dict = {}

_lemma_client: Optional[anthropic.Anthropic] = None


def _get_known_forms_cache(language: str) -> set[str]:
    if language not in _known_forms_cache_by_lang:
        path = _known_forms_cache_file(language)
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    _known_forms_cache_by_lang[language] = set(json.load(f))
                    return _known_forms_cache_by_lang[language]
            except Exception:
                pass
        _known_forms_cache_by_lang[language] = set()
    return _known_forms_cache_by_lang[language]


def _save_known_forms_cache(language: str) -> None:
    cache = _known_forms_cache_by_lang.get(language, set())
    with open(_known_forms_cache_file(language), 'w', encoding='utf-8') as f:
        json.dump(sorted(cache), f, ensure_ascii=False)


def _get_lemma_cache(language: str) -> dict[str, str]:
    if language not in _lemma_cache_by_lang:
        path = _lemma_cache_file(language)
        if os.path.exists(path):
            try:
                with open(path, encoding='utf-8') as f:
                    _lemma_cache_by_lang[language] = json.load(f)
                    return _lemma_cache_by_lang[language]
            except Exception:
                pass
        _lemma_cache_by_lang[language] = {}
    return _lemma_cache_by_lang[language]


def _save_lemma_cache(language: str) -> None:
    cache = _lemma_cache_by_lang.get(language, {})
    with open(_lemma_cache_file(language), 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _get_lemma_client() -> anthropic.Anthropic:
    global _lemma_client
    if _lemma_client is None:
        _env = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(_env):
            with open(_env) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())
        _lemma_client = anthropic.Anthropic()
    return _lemma_client


# ─── Public LLM-based functions ───────────────────────────────────────────────

def lemmatize_words(words: list[str], language: str = "hebrew") -> dict[str, str]:
    """Return the base/dictionary form for each word using LLM + persistent cache.

    Results are cached per language so each unique word is only sent to the LLM once.
    """
    lemma_cache = _get_lemma_cache(language)
    uncached = [w for w in words if w not in lemma_cache]
    if uncached:
        client = _get_lemma_client()
        words_str = "\n".join(f"- {w}" for w in uncached)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{
                "role": "user",
                "content": f"""For each {language} word, return the standalone base form by stripping any leading grammatical prefix (conjunctions, prepositions, articles that attach as prefixes). Do NOT change the core form, tense, number, or gender — just remove the grammatical prefix if present.

If no prefix, return the word as-is.

Words:
{words_str}

Respond with JSON only, one key per input word: {{"word": "base_form", ...}}"""
            }]
        )
        result = _parse_json_response(response.content[0].text)
        for w in uncached:
            lemma_cache[w] = result.get(w, w)
        _save_lemma_cache(language)
    return {w: lemma_cache.get(w, w) for w in words}


def get_lemma(word: str, language: str = "hebrew") -> str:
    """Return the base form for a single word (LLM + cache)."""
    return lemmatize_words([word], language)[word]


def check_violations_llm(words: list[str], known_words: list[str], language: str = "hebrew") -> list[str]:
    """Return which words are not morphological variants of any known word.

    Three-tier cache (fastest to slowest):
      1. Literal match against known_words (instant)
      2. known_forms_cache — disk-persisted confirmed valid forms (instant, per-language)
      3. violation_cache — in-memory confirmed violations for this session (instant)
      4. LLM — batch call for anything not yet seen
    Non-violations are written to disk and never need re-checking.
    Violations are session-only (a violation may become valid once that word is learned).
    """
    known_set = set(known_words)
    known_forms_cache = _get_known_forms_cache(language)

    # Tier 1: literal match
    suspicious = [w for w in words if w not in known_set]
    if not suspicious:
        return []

    # Tier 2: disk cache — confirmed valid forms
    suspicious = [w for w in suspicious if w not in known_forms_cache]
    if not suspicious:
        return []

    # Tier 3: in-memory violation cache for this session's vocabulary
    known_key = frozenset(known_words)
    uncached = [w for w in suspicious if (w, known_key, language) not in _violation_cache]

    if uncached:
        client = _get_lemma_client()
        known_str = ", ".join(known_words)
        words_str = "\n".join(f"- {w}" for w in uncached)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Known {language} vocabulary: {known_str}

For each word below, is it a morphological variant of any word in the known vocabulary? (Include all conjugations, gender/number forms, and grammatical affixes such as conjunctions, prepositions, articles, etc. that attach to words in this language.)

Words to check:
{words_str}

Return JSON only: {{"violations": ["word1", ...]}} — list ONLY words that are NOT variants of any known word."""
            }]
        )
        result = _parse_json_response(response.content[0].text)
        violations_set = set(result.get("violations", []))
        cache_updated = False
        for w in uncached:
            if w in violations_set:
                _violation_cache[(w, known_key, language)] = True
            else:
                known_forms_cache.add(w)
                cache_updated = True
        if cache_updated:
            _save_known_forms_cache(language)

    return [w for w in suspicious if _violation_cache.get((w, known_key, language), False)]


def detect_due_words_llm(text: str, due_words: list[str], language: str = "hebrew") -> list[str]:
    """Return which due_words appeared in the text in any morphological form."""
    if not due_words:
        return []
    if not text.strip():
        return []
    client = _get_lemma_client()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""Text: {text}

Vocabulary: {", ".join(due_words)}

Which vocabulary words appear in the text in any morphological form (conjugation, gender, number, tense, affix, etc.)?

Return JSON only: {{"found": ["word1", ...]}} listing only vocabulary words that appear."""
        }]
    )
    return _parse_json_response(response.content[0].text).get("found", [])


# ─── Utility ──────────────────────────────────────────────────────────────────

def _load_static_dict() -> dict[str, list[str]]:
    return _static_dict


def _load_overflow_cache() -> dict[str, list[str]]:
    if os.path.exists(OVERFLOW_CACHE_FILE):
        try:
            with open(OVERFLOW_CACHE_FILE, encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_overflow_cache(cache: dict[str, list[str]]) -> None:
    with open(OVERFLOW_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _strip_nikud(text: str) -> str:
    """Remove Hebrew vowel marks (U+05B0–U+05C7) from text."""
    return re.sub(r'[\u05B0-\u05C7]', '', text)


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        start = text.find('{')
        if start == -1:
            return {}
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except Exception:
                        return {}
        return {}


# ─── Hebrew dictionary expansion (build-time only) ───────────────────────────

def _expand_verb(verb: str, client: anthropic.Anthropic) -> list[str]:
    """Expand a Hebrew verb with two rounds: initial conjugation table, then a gap-fill check."""

    r1 = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        messages=[{
            "role": "user",
            "content": f"""You are a Hebrew morphology expert. Conjugate the verb: {verb}

{verb} belongs to a specific binyan. Generate ONLY forms of that exact binyan — not passive or derived binyanim.
Example: לדבר (Pi'el) → present is מדבר/מדברת (NOT דובר/דוברת which is Pu'al).

IMPORTANT: Write all forms WITHOUT nikud (no vowel marks). Plain Hebrew consonants only.

Fill in EVERY cell:
PRESENT (בינוני) — 4 forms: m.s., f.s., m.p., f.p.
PAST (עבר) — 9 forms: 3m.s., 3f.s., 2m.s., 2f.s., 1s., 3p., 2m.p., 2f.p., 1p.
FUTURE (עתיד) — 9 forms: 3m.s., 3f.s., 2m.s., 2f.s., 1s., 3p., 2m.p., 2f.p., 1p.
IMPERATIVE (ציווי) — 3 forms: m.s., f.s., p.
INFINITIVE: {verb}

Respond with JSON only: {{"forms": ["form1", "form2", ...]}}"""
        }]
    )
    round1 = set(_parse_json_response(r1.content[0].text).get("forms", []))
    round1.add(verb)

    forms_str = ", ".join(sorted(round1))
    r2 = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": f"""You are a Hebrew morphology expert.

For the verb {verb}, these forms have already been collected:
{forms_str}

A complete conjugation has 4 present forms, 9 past forms, 9 future forms, 3 imperative forms.
List ONLY the forms that are genuinely missing from the above list.
Write all forms WITHOUT nikud (plain consonants only). If nothing is missing, return {{"missing": []}}.

Respond with JSON only: {{"missing": ["form1", "form2", ...]}}"""
        }]
    )
    missing = set(_parse_json_response(r2.content[0].text).get("missing", []))

    all_forms = round1 | missing
    return sorted(_strip_nikud(f) for f in all_forms)


def _expand_non_verbs(words: list[str], client: anthropic.Anthropic) -> dict[str, list[str]]:
    """Expand Hebrew nouns, adjectives, and particles in a batch."""
    words_str = "\n".join(f"- {w}" for w in words)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=3000,
        messages=[{
            "role": "user",
            "content": f"""You are a Hebrew morphology expert.

Write all forms WITHOUT nikud (plain consonants only).

For each word below list ALL valid surface forms:
- NOUNS: base form, plural, construct state, AND with every possessive suffix on BOTH singular and plural:
  Singular possessed: +י (e.g. ספרי), +ך, +ו, +ה, +נו, +כם, +כן, +הם, +הן
  Plural possessed: +יי (e.g. ספריי = my books), +יך, +יו, +יה, +ינו, +יכם, +יכן, +יהם, +יהן
- ADJECTIVES: exactly 4 forms — m.s., f.s., m.p., f.p. (no possessive suffixes)
- PARTICLES/PRONOUNS/ADVERBS: just the word itself (no variants)

Words:
{words_str}

Respond with JSON only — no markdown fences:
{{"forms": {{"word": ["form1", "form2"]}}}}"""
        }]
    )
    result = _parse_json_response(response.content[0].text)
    raw = result.get("forms", {})
    out: dict[str, list[str]] = {}
    for word in words:
        forms = list(raw.get(word, [word]))
        if word not in forms:
            forms.append(word)
        out[word] = forms
    return out


def _classify_words(words: list[str], client: anthropic.Anthropic) -> dict[str, bool]:
    """Ask the LLM to classify each Hebrew word as verb infinitive or not."""
    words_str = "\n".join(f"- {w}" for w in words)
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""For each Hebrew word below, answer true if it is a verb infinitive (starts with ל and is an infinitive form), false otherwise (preposition, pronoun, adverb, conjunction, etc.).

Words:
{words_str}

Respond with JSON only: {{"classifications": {{"word": true_or_false}}}}"""
        }]
    )
    result = _parse_json_response(response.content[0].text)
    return result.get("classifications", {})


def _is_verb(word: str) -> bool:
    """Preliminary filter: must start with ל and have no spaces to even be considered."""
    return ' ' not in word and word.startswith('ל')


def _expand_compound(compound: str, client: anthropic.Anthropic) -> list[str]:
    """Expand a Hebrew multi-word compound (e.g. 'בית ספר') into all its surface forms."""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": f"""You are a Hebrew morphology expert.

List ALL surface forms of the compound word: {compound}
Include: base form, definite form, plural, plural definite, and with common possessive suffixes.
Write WITHOUT nikud (plain consonants only).

Respond with JSON only: {{"forms": ["form1", "form2", ...]}}"""
        }]
    )
    result = _parse_json_response(response.content[0].text)
    forms = [_strip_nikud(f) for f in result.get("forms", [])]
    if compound not in forms:
        forms.append(compound)
    return forms


def _expand_words(words: list[str], client: anthropic.Anthropic, verbose: bool = False) -> dict[str, list[str]]:
    """Expand a list of Hebrew words into their morphological forms via LLM."""
    compounds = [w for w in words if ' ' in w]
    candidates = [w for w in words if _is_verb(w)]
    non_lamed = [w for w in words if not _is_verb(w) and ' ' not in w]

    if candidates:
        classifications = _classify_words(candidates, client)
    else:
        classifications = {}
    verbs = [w for w in candidates if classifications.get(w, False)]
    non_verbs = non_lamed + [w for w in candidates if not classifications.get(w, False)]
    out: dict[str, list[str]] = {}

    for compound in compounds:
        if verbose:
            print(f"  [expand] compound: {compound}")
        out[compound] = _expand_compound(compound, client)

    for verb in verbs:
        if verbose:
            print(f"  [expand] verb: {verb}")
        out[verb] = _expand_verb(verb, client)

    if non_verbs:
        batches = [non_verbs[i:i+NOUN_BATCH_SIZE] for i in range(0, len(non_verbs), NOUN_BATCH_SIZE)]
        for i, batch in enumerate(batches):
            if verbose:
                print(f"  [expand] nouns/adj batch {i+1}/{len(batches)}: {', '.join(batch)}")
            out.update(_expand_non_verbs(batch, client))

    return out


def _collect_forms(word: str, forms: list[str], all_forms: set[str]) -> None:
    """Add all forms to the set, and for compounds also add individual tokens."""
    for form in forms:
        all_forms.add(form)
        if ' ' in form:
            for token in re.findall(r'[\u05D0-\u05EA]+', form):
                all_forms.add(token)


def load_known_forms(known_words: list[str], verbose: bool = False) -> set[str]:
    """Return the expanded forms set for known_words from the Hebrew static dictionary.

    For non-Hebrew words (not in the static dict), returns the words themselves.
    """
    static = _load_static_dict()

    all_forms: set[str] = set()
    for word in known_words:
        if word in static:
            forms = static[word]
        elif word in _reverse_index:
            forms = static[_reverse_index[word]]
        else:
            forms = [word]
        _collect_forms(word, forms, all_forms)

        # One-level transitive expansion (Hebrew only)
        for f in forms:
            if isinstance(f, str) and ' ' not in f and f in static and f != word:
                _collect_forms(f, static[f], all_forms)

    return all_forms
