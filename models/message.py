from datetime import datetime
from pydantic import BaseModel

class Message(BaseModel):
    user_id: str
    role: str  # "user" | "ai" | "tool"
    content: dict | str
    created_at: datetime