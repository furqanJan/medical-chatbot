import uuid
import bcrypt
from db import get_db


# =========================
# USER AUTH
# =========================

def authenticate(username: str, password: str) -> bool:
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT password_hash FROM users WHERE username=?",
        (username,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return False

    stored_hash = row["password_hash"]

    # Google OAuth users have plain "google_oauth" stored — skip bcrypt
    if stored_hash == "google_oauth":
        return False

    return bcrypt.checkpw(
        password.encode(),
        stored_hash.encode()
    )


def create_user(username: str, password: str) -> bool:
    if password == "google_oauth":
        password_hash = "google_oauth"
    else:
        password_hash = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
        conn.commit()
        conn.close()
        return True
    except Exception:
        # Username already exists — silently pass for Google re-login
        return False


# =========================
# SESSION (in-memory)
# =========================

_SESSIONS = {}


def create_session(username: str) -> str:
    session_id = str(uuid.uuid4())
    _SESSIONS[session_id] = username
    return session_id


def get_user_from_session(session_id: str):
    return _SESSIONS.get(session_id)


def delete_session(session_id: str):
    _SESSIONS.pop(session_id, None)