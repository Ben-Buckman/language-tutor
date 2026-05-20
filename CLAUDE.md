# Language Tutor

AI-powered language learning app. Users have constrained conversations with Claude — the AI only uses words the user already knows, gradually teaching new vocabulary through spaced repetition (SRS).

## Architecture

```
language-tutor/
├── server.py          # FastAPI backend — main entry point
├── engine.py          # Claude AI chat + vocabulary constraint logic
├── srs.py             # Spaced repetition system (pure functions, stateless)
├── forms_cache.py     # Morphological forms + lemmatization (Hebrew/EN/ES)
├── dictionaries/he.json  # Static Hebrew dictionary (~2000 words)
├── requirements.txt
├── Procfile           # Railway deploy: uvicorn server:app --host 0.0.0.0 --port $PORT
├── mobile/            # React Native / Expo frontend
│   ├── App.tsx        # Root — manages knownWords + wordData state per language
│   ├── screens/ConversationScreen.tsx
│   ├── screens/WordListScreen.tsx
│   ├── srsStorage.ts  # AsyncStorage helpers for SRS data
│   └── constants.ts   # API_BASE, language configs, default word lists
└── redeploy.ps1       # One-command deploy script (see below)
```

## Key design decisions

- **SRS state lives in the client** (AsyncStorage). `word_data` is passed in every API request and returned updated in the response. The backend is stateless — no per-user files.
- **Backend caches** (lemma_cache.json, known_forms_cache.json) are shared across users and ephemeral — they rebuild automatically on cold start.
- **Hebrew morphology** uses a static dictionary with LLM fallback; English/Spanish are LLM-only.

## Deployed URLs

- **Frontend**: https://language-tutor-ben.netlify.app
- **Backend**: https://backend-production-4c9d.up.railway.app

## API endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/chat` | Send message, get AI response + updated SRS data |
| POST | `/words/stats` | Get SRS stats for a word list |
| POST | `/words/all-forms` | Get all morphological forms for known words |
| POST | `/words/lemmatize` | Normalize words to canonical lemmas |
| GET  | `/health` | Health check |

All chat/stats endpoints accept `word_data: dict` (the user's SRS state) and `/chat` returns it updated.

## How to redeploy after making changes

Run from the project root:

```powershell
.\redeploy.ps1 -Message "describe what changed"
```

This script:
1. Commits and pushes to GitHub → Railway auto-redeploys the backend
2. Builds the Expo web app (`npx expo export --platform web`)
3. Zips and uploads the `dist/` folder to Netlify

**Important**: The zip must use Unix forward-slash paths (not Windows backslashes) or Netlify won't extract the `_expo/` directory correctly. The script handles this.

## Local development

```powershell
# Backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Frontend (in a separate terminal)
cd mobile
$env:EXPO_PUBLIC_API_BASE = "http://localhost:8000"
npx expo start --web
```

## Environment variables

- **Railway** (backend): `ANTHROPIC_API_KEY`
- **Frontend build**: `EXPO_PUBLIC_API_BASE` — set in `netlify.toml` for production, or `.env` for local dev
