from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from engine import chat, check_violations, detect_due_words_used
from srs import get_due_words, record_exposures, get_word_stats
from forms_cache import load_known_forms, get_lemma

# Conversation logger — writes to chat.log
chat_logger = logging.getLogger("chat")
chat_logger.setLevel(logging.DEBUG)
_handler = logging.FileHandler("chat.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(message)s"))
chat_logger.addHandler(_handler)

def log_turn(user: str, assistant: str, attempts: int, new_words: list[str], clean: bool, language: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chat_logger.info(f"\n[{ts}] [{language}]")
    chat_logger.info(f"  USER:      {user}")
    chat_logger.info(f"  AI:        {assistant}")
    chat_logger.info(f"  attempts={attempts}  clean={clean}  new_words={new_words or '—'}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    user_input: str
    history: list[Message]
    known_words: list[str]
    language: str = "hebrew"
    word_data: dict = {}  # SRS data keyed by word, owned by the client


class ChatResponse(BaseModel):
    response: str
    history: list[Message]
    attempts: int
    clean: bool
    new_words: list[str]
    word_data: dict  # Updated SRS data to be saved by the client


class WordStats(BaseModel):
    word: str
    exposures: int
    interval: int
    due_date: str
    last_seen: Optional[str]
    due: bool
    days_until_due: int


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    if not req.user_input.strip():
        raise HTTPException(status_code=400, detail="user_input is empty")
    if not req.known_words:
        raise HTTPException(status_code=400, detail="known_words is empty")

    history_dicts = [{"role": m.role, "content": m.content} for m in req.history]

    # Log a session boundary when the user starts a fresh conversation
    if not req.history:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        chat_logger.info(f"\n{'='*60}\n=== NEW SESSION [{ts}] [{req.language}] ===\n{'='*60}")

    due_words = get_due_words(req.known_words, req.word_data)

    response, updated_history, attempts, _, new_words = chat(
        req.user_input, history_dicts, req.known_words, req.language, due_words
    )

    # Track all known words that appeared in either the user's message or AI response
    combined_text = req.user_input + " " + response
    words_seen = detect_due_words_used(combined_text, req.known_words, req.language)
    updated_word_data = record_exposures(words_seen, req.word_data) if words_seen else req.word_data

    all_known = set(req.known_words) | set(new_words)
    violations = check_violations(response, list(all_known), req.language)

    log_turn(req.user_input, response, attempts, new_words, len(violations) == 0, req.language)

    return ChatResponse(
        response=response,
        history=[Message(role=m["role"], content=m["content"]) for m in updated_history],
        attempts=attempts,
        clean=len(violations) == 0,
        new_words=new_words,
        word_data=updated_word_data,
    )


class WordsRequest(BaseModel):
    words: list[str]
    language: str = "hebrew"
    word_data: dict = {}  # SRS data owned by the client


@app.post("/words/stats", response_model=list[WordStats])
def word_stats(req: WordsRequest):
    if not req.words:
        raise HTTPException(status_code=400, detail="no words provided")
    return get_word_stats(req.words, req.word_data)


@app.post("/words/all-forms")
def all_forms(req: WordsRequest):
    """Returns the flat set of all morphological forms for the given known words."""
    if not req.words:
        raise HTTPException(status_code=400, detail="no words provided")
    forms = load_known_forms(req.words)
    return list(forms)


@app.post("/words/lemmatize")
def lemmatize(req: WordsRequest):
    """Return the canonical lemma for each word in the list."""
    if not req.words:
        raise HTTPException(status_code=400, detail="no words provided")
    from forms_cache import lemmatize_words
    result = lemmatize_words(req.words, req.language)
    return [result[w] for w in req.words]


@app.get("/health")
def health():
    return {"status": "ok"}
