from __future__ import annotations
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from engine import chat
from srs import get_word_stats
from forms_cache import load_known_forms, lemmatize_words

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    user_input: str
    history: list[Message]


class ChatResponse(BaseModel):
    response: str
    history: list[Message]


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    if not req.user_input.strip():
        raise HTTPException(status_code=400, detail="user_input is empty")

    history_dicts = [{"role": m.role, "content": m.content} for m in req.history]
    response, updated_history = chat(req.user_input, history_dicts)

    return ChatResponse(
        response=response,
        history=[Message(role=m["role"], content=m["content"]) for m in updated_history],
    )


class WordsRequest(BaseModel):
    words: list[str]
    language: str = "hebrew"
    word_data: dict = {}


class WordStats(BaseModel):
    word: str
    exposures: int
    interval: int
    due_date: str
    last_seen: Optional[str]
    due: bool
    days_until_due: int


@app.post("/words/stats", response_model=list[WordStats])
def word_stats(req: WordsRequest):
    if not req.words:
        raise HTTPException(status_code=400, detail="no words provided")
    return get_word_stats(req.words, req.word_data)


@app.post("/words/all-forms")
def all_forms(req: WordsRequest):
    if not req.words:
        raise HTTPException(status_code=400, detail="no words provided")
    return list(load_known_forms(req.words))


@app.post("/words/lemmatize")
def lemmatize(req: WordsRequest):
    if not req.words:
        raise HTTPException(status_code=400, detail="no words provided")
    result = lemmatize_words(req.words, req.language)
    return [result[w] for w in req.words]


@app.get("/health")
def health():
    return {"status": "ok"}
