# backend/memory.py


class ContextMemory:
    def __init__(self, max_turns: int = 5):
        self.max_turns = max_turns
        self.store = {}

    def add(self, session_id: str, question: str, answer: str):
        if session_id not in self.store:
            self.store[session_id] = []

        self.store[session_id].append((question, answer))

        # Keep only last N turns
        if len(self.store[session_id]) > self.max_turns:
            self.store[session_id].pop(0)

    def get_context(self, session_id: str) -> str:
        history = self.store.get(session_id, [])
        context = ""
        for q, a in history:
            context += f"User: {q}\nAssistant: {a}\n"
        return context

    def clear(self, session_id: str):
        self.store[session_id] = []