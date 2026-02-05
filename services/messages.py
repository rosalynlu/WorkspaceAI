from datetime import datetime, timezone
from bson import ObjectId
from db import messages_collection

def create_message(user_id: str, role: str, content):
    doc = {
        "user_id": user_id,
        "role": role,  # "user" | "assistant" | "tool"
        "content": content,
        "created_at": datetime.now(timezone.utc),
    }
    res = messages_collection.insert_one(doc)
    doc["_id"] = res.inserted_id
    return doc

def serialize_message(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": doc["user_id"],
        "role": doc["role"],
        "content": doc["content"],
        "created_at": doc["created_at"].isoformat() if doc.get("created_at") else None,
    }

def list_messages(user_id: str, limit: int = 50):
    cur = (
        messages_collection
        .find({"user_id": user_id})
        .sort("created_at", -1)
        .limit(limit)
    )
    return [serialize_message(d) for d in cur]

def get_message(user_id: str, message_id: str):
    doc = messages_collection.find_one({"_id": ObjectId(message_id), "user_id": user_id})
    return serialize_message(doc) if doc else None