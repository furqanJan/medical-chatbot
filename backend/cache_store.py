# backend/cache_store.py

_cache = {}


def get_from_cache(key: str):
    return _cache.get(key.strip().lower())


def save_to_cache(key: str, value: str):
    _cache[key.strip().lower()] = value


def clear_cache():
    _cache.clear()