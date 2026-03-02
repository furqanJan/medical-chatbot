# backend/langgraph_flow.py
# Lightweight relevance gate — no LangGraph dependency required.
# Returns True if retrieved chunks have enough content to answer.


def should_answer(chunks: list) -> bool:
    if not chunks:
        return False

    joined = " ".join(chunks).lower()

    # Reject if combined evidence is too short
    if len(joined.strip()) < 50:
        return False

    return True