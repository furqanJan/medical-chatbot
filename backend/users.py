# backend/users.py
# Legacy stub — kept for reference only.
# Real auth is handled by auth.py + SQLite.

USERS = {}


def verify_user(username: str, password: str):
    user = USERS.get(username)
    if not user:
        return None
    if user["password"] != password:
        return None
    return user