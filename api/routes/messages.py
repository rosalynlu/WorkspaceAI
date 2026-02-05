from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from dependencies.auth import get_current_user_id
from services.messages import create_message, list_messages, get_message

router = APIRouter()

class MessageCreate(BaseModel):
    role: str
    content: dict | str

@router.post("/messages")
def post_message(payload: MessageCreate, user_id: str = Depends(get_current_user_id)):
    doc = create_message(user_id=user_id, role=payload.role, content=payload.content)
    return {"status": "ok", "message_id": str(doc["_id"])}

@router.get("/messages")
def get_messages(limit: int = 50, user_id: str = Depends(get_current_user_id)):
    return {"status": "ok", "messages": list_messages(user_id=user_id, limit=min(limit, 200))}

@router.get("/messages/{message_id}")
def get_one_message(message_id: str, user_id: str = Depends(get_current_user_id)):
    msg = get_message(user_id=user_id, message_id=message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"status": "ok", "message": msg}