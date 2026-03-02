from pymongo import MongoClient
from datetime import datetime

# MongoDB connection
client = MongoClient("mongodb://127.0.0.1:27017")
db = client["furqii_chatbot"]

chat_history_collection = db["chat_history"]
sessions_collection = db["sessions"]

def save_message(session_id: str, role: str, content: str):
    """Saves a message and ensures the session title exists for the sidebar."""
    chat_history_collection.insert_one({
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    })
    
    # Update sidebar: If it's a new session, the first message becomes the title
    sessions_collection.update_one(
        {"session_id": session_id},
        {
            "$set": {"last_updated": datetime.utcnow()},
            "$setOnInsert": {"title": content[:30] + "..." if len(content) > 30 else content}
        },
        upsert=True
    )

def load_session_history(session_id: str, limit: int = 50):
    """Retrieves chat history for the main chat window."""
    return list(chat_history_collection.find({"session_id": session_id}, {"_id": 0}).sort("timestamp", 1).limit(limit))

def get_all_sessions():
    """Retrieves all sessions for the sidebar list."""
    return list(sessions_collection.find({}, {"_id": 0}).sort("last_updated", -1))