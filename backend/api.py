import os
from typing import List, Optional, Any

from fastapi import FastAPI, Header, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from pinecone_rag import PineconeRAG
from google_auth import verify_google_token

# Import MongoDB logic
from mongo_db import (
    save_message,
    load_session_history,
    get_all_sessions
)

from auth import (
    authenticate,
    create_session,
    get_user_from_session,
    create_user,
    delete_session,
)

from cache_store import get_from_cache, save_to_cache
from memory import ContextMemory
from langgraph_flow import should_answer
from llm_engine import ask_llm


# =====================================
# App Init
# =====================================
app = FastAPI(title="Furqii Chat Bot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================
# Core Components
# =====================================
rag = PineconeRAG()
memory = ContextMemory(max_turns=5)


# =====================================
# Schemas
# =====================================
class Question(BaseModel):
    question: str

class LoginRequest(BaseModel):
    username: str
    password: str

class SignupRequest(BaseModel):
    username: str
    password: str


# =====================================
# Helpers (FIXED PROMPT STRUCTURE)
# =====================================
def build_prompt(question: str, context: str, chunks: List[str]) -> str:
    evidence = "\n\n".join(chunks)

    return f"""
### SYSTEM INSTRUCTION
You are a medical assistant named Furqii. 
Answer the user's question based ONLY on the WHO EVIDENCE provided below.
If the answer is not present in the evidence, state: "I don't have enough information in the document."
Keep the answer concise and professional.

### CONVERSATION HISTORY (FOR CONTEXT)
{context}

### WHO MEDICAL EVIDENCE (USE THIS TO ANSWER)
{evidence}

### USER QUESTION
{question}

### FINAL RESPONSE:
""".strip()


def _row_get(row: Any, key: str, default=None):
    try:
        if isinstance(row, dict):
            return row.get(key, default)
        return getattr(row, key, default)
    except Exception:
        return default


# =====================================
# Health & Sessions
# =====================================
@app.get("/")
def root():
    return {"status": "ok", "message": "Furqii Chat Bot API running"}

@app.get("/sessions")
def fetch_sessions():
    return {"sessions": get_all_sessions()}


# =====================================
# SIGNUP / LOGIN
# =====================================
@app.post("/signup")
def signup(payload: SignupRequest):
    success = create_user(payload.username, payload.password)
    if not success:
        return {"error": "Username already exists"}
    return {"message": "User created successfully"}


@app.post("/login")
def login(payload: LoginRequest):
    if not authenticate(payload.username, payload.password):
        return {"error": "Invalid username or password"}

    session_id = create_session(payload.username)

    return {
        "message": "Login successful",
        "session_id": session_id,
        "user": payload.username,
    }


# =====================================
# ASK (Core RAG Logic)
# =====================================
@app.post("/ask")
def ask(payload: Question, x_session_id: Optional[str] = Header(None)):

    q_raw = (payload.question or "").strip()
    
    # Improved Small Talk cleaning
    q_clean = q_raw.lower().strip(" '\"!?.")

    if not q_clean:
        return {"answer": "Please ask a medical question."}

    # Small Talk check
    if q_clean in {"hi", "hello", "hey", "who are you", "how are you", "thanks"}:
        return {"answer": "Hello 👋 I'm Furqii — a WHO-based medical assistant. Ask me about respiratory diseases!"}

    if not x_session_id:
        return {"error": "Login required. Please login first."}

    user = get_user_from_session(x_session_id)
    if not user:
        return {"error": "Invalid or expired session. Please login again."}

    # 1. Cache check
    cached = get_from_cache(q_raw)
    if cached:
        return {"answer": cached, "source": "cache"}

    # 2. Pinecone RAG search
    results = rag.search(q_raw, k=3)

    # LOWERED THRESHOLD: 0.3 is better for this specific model
    valid_results = [r for r in results if r.get('score', 0) > 0.3]

    if not valid_results:
        return {"answer": "I don't have enough information in the document to answer that question."}

    chunks = [r["content"] for r in valid_results]

    # 3. Build conversation context
    history_rows = load_session_history(x_session_id, limit=3)
    db_context = ""
    for row in history_rows:
        role = _row_get(row, "role", "user")
        content = _row_get(row, "content", "")
        db_context += f"{str(role).capitalize()}: {content}\n"

    # 4. LLM generation
    prompt = build_prompt(q_raw, db_context, chunks)
    llm_answer = ask_llm(prompt)

    final_answer = (
        f"{llm_answer}\n\n"
        "⚠️ Safety note: If symptoms are severe, please seek immediate medical care."
    )

    # 5. Persist to MongoDB + memory + cache
    save_message(x_session_id, "user", q_raw)
    save_message(x_session_id, "assistant", final_answer)
    save_to_cache(q_raw, final_answer)

    return {
        "answer": final_answer,
        "chunks_used": len(chunks),
        "source": "pinecone+llm",
    }


# =====================================
# HISTORY
# =====================================
@app.get("/history")
def get_chat_history(x_session_id: Optional[str] = Header(None), limit: int = 50):
    if not x_session_id:
        return {"error": "Session ID missing"}

    user = get_user_from_session(x_session_id)
    if not user:
        return {"error": "Invalid session"}

    rows = load_session_history(x_session_id, limit=limit)

    history = [
        {
            "role": _row_get(row, "role", ""),
            "content": _row_get(row, "content", ""),
            "timestamp": _row_get(row, "timestamp", None),
        }
        for row in rows
    ]

    return {
        "total_messages": len(history),
        "history": history,
    }


# =====================================
# RESET
# =====================================
@app.post("/reset")
def reset_chat(x_session_id: Optional[str] = Header(None)):
    if not x_session_id:
        return {"error": "Session ID missing"}

    from mongo_db import chat_history_collection, sessions_collection
    
    chat_history_collection.delete_many({"session_id": x_session_id})
    sessions_collection.delete_one({"session_id": x_session_id})

    memory.clear(x_session_id)
    return {"message": "Chat reset successful"}


# =====================================
# LOGOUT
# =====================================
@app.post("/logout")
def logout(x_session_id: Optional[str] = Header(None)):
    if x_session_id:
        delete_session(x_session_id)
        memory.clear(x_session_id)

    return {"message": "Logged out successfully"}