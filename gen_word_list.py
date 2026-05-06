import anthropic, json, os, re
from dotenv import load_dotenv
load_dotenv()

client = anthropic.Anthropic()
resp = client.messages.create(
    model='claude-sonnet-4-6',
    max_tokens=4000,
    messages=[{'role': 'user', 'content': '''List the 500 most common modern Hebrew words used in everyday conversation. Include: common verbs (infinitive form with ל), nouns, adjectives, pronouns, prepositions, conjunctions, question words, time words, numbers 1-10. Focus on frequency in spoken and written modern Hebrew. No nikud (vowel marks). Return JSON only, no markdown: {"words": ["word1", "word2", ...]}'''}]
)
raw = resp.content[0].text.strip()
# Strip markdown code fences if present
raw = re.sub(r'^```[a-z]*\n?', '', raw)
raw = re.sub(r'\n?```$', '', raw)
data = json.loads(raw)
words = data['words']
print(f'Got {len(words)} words')
with open('word_list_500.py', 'w', encoding='utf-8') as f:
    f.write('KNOWN_WORDS_500 = [\n')
    for w in words:
        f.write(f'    "{w}",\n')
    f.write(']\n')
print('Saved to word_list_500.py')
