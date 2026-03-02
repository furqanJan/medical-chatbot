# backend/llm_engine.py

import os
import requests
from dotenv import load_dotenv

load_dotenv()

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "tinyllama")
OLLAMA_URL = "http://localhost:11434/api/chat"


def ask_llm(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        return r.json()["message"]["content"].strip()

    except requests.exceptions.ConnectionError:
        return (
            "⚠️ Ollama server is not running. "
            "Start it with: ollama serve"
        )
    except requests.exceptions.Timeout:
        return "⚠️ LLM timeout. Model may still be loading."
    except Exception as e:
        return f"⚠️ LLM error: {str(e)}"