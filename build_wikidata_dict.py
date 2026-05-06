"""
build_wikidata_dict.py — Downloads the Wikidata lexemes dump and extracts all
Hebrew lexemes (lemma → surface forms) into dictionaries/he.json.

Run: python build_wikidata_dict.py

The dump is ~1-2 GB compressed. It streams line-by-line so memory usage is low.
Only Hebrew entries (language Q9288) are kept. Everything else is skipped.
"""
import sys, json, gzip, re, os
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

DUMP_URL = "https://dumps.wikimedia.org/wikidatawiki/entities/latest-lexemes.json.gz"
OUT_FILE = os.path.join(os.path.dirname(__file__), "dictionaries", "he.json")
HEBREW_LANG = "Q9288"
SAVE_EVERY = 5000  # save progress every N Hebrew entries


def strip_nikud(text: str) -> str:
    """Remove Hebrew vowel marks and cantillation so forms match plain text."""
    return re.sub(r'[\u0591-\u05C7\uFB1D-\uFB4E]', '', text).strip()


def main():
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

    # Resume from existing file if present
    if os.path.exists(OUT_FILE):
        with open(OUT_FILE, encoding='utf-8') as f:
            result = json.load(f)
        print(f"Resuming — {len(result)} entries already in dictionary.")
    else:
        result = {}

    print(f"Streaming dump from Wikidata...")
    print(f"URL: {DUMP_URL}")
    print(f"Output: {OUT_FILE}")
    print()

    total = 0
    hebrew = 0

    req = urllib.request.Request(DUMP_URL, headers={"User-Agent": "HebrewTutorApp/1.0"})

    with urllib.request.urlopen(req, timeout=30) as response:
        with gzip.GzipFile(fileobj=response) as gz:
            for raw_line in gz:
                line = raw_line.decode('utf-8').strip()

                # Wikidata dump format: JSON array, one entity per line, with trailing comma
                if not line or line in ('[', ']'):
                    continue
                if line.endswith(','):
                    line = line[:-1]

                try:
                    entity = json.loads(line)
                except json.JSONDecodeError:
                    continue

                total += 1
                if total % 50000 == 0:
                    print(f"  {total:,} lexemes scanned, {hebrew:,} Hebrew found...")

                if entity.get('language') != HEBREW_LANG:
                    continue

                hebrew += 1

                # --- Extract lemma ---
                lemma_val = entity.get('lemmas', {}).get('he', {}).get('value', '')
                lemma = strip_nikud(lemma_val)
                if not lemma:
                    continue

                # --- Extract all surface forms ---
                forms: set[str] = {lemma}
                for form in entity.get('forms', []):
                    for lang_code, rep in form.get('representations', {}).items():
                        if lang_code.startswith('he'):
                            val = strip_nikud(rep.get('value', ''))
                            if val:
                                forms.add(val)

                # Merge into result
                if lemma in result:
                    result[lemma] = sorted(set(result[lemma]) | forms)
                else:
                    result[lemma] = sorted(forms)

                # Save progress periodically
                if hebrew % SAVE_EVERY == 0:
                    with open(OUT_FILE, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)
                    print(f"  Saved {len(result)} entries ({hebrew} Hebrew lexemes processed)")

    # Final save
    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    total_forms = sum(len(v) for v in result.values())
    print(f"\nDone!")
    print(f"  Hebrew lexemes: {hebrew:,}")
    print(f"  Dictionary entries: {len(result):,}")
    print(f"  Total surface forms: {total_forms:,}")
    print(f"  Avg forms per lemma: {total_forms / max(len(result), 1):.1f}")
    print(f"  Saved to: {OUT_FILE}")


if __name__ == '__main__':
    main()
