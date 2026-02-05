from datetime import datetime, timezone
from bson import ObjectId
from db import action_requests_collection

def create_action_request(user_id: str, user_message: str, plans: list, confirmation_message: str):
    doc = {
        "user_id": user_id,
        "status": "pending",  # pending | approved | canceled | executed | failed
        "user_message": user_message,
        "plans": plans,
        "confirmation_message": confirmation_message,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    res = action_requests_collection.insert_one(doc)
    return str(res.inserted_id)

def get_action_request(user_id: str, action_request_id: str):
    return action_requests_collection.find_one({"_id": ObjectId(action_request_id), "user_id": user_id})

def mark_action_request(action_request_id: str, user_id: str, status: str, extra: dict | None = None):
    update = {"status": status, "updated_at": datetime.now(timezone.utc)}
    if extra:
        update.update(extra)
    action_requests_collection.update_one(
        {"_id": ObjectId(action_request_id), "user_id": user_id},
        {"$set": update},
    )