from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    password: str
    email: EmailStr | None = None

class UserInDB(BaseModel):
    user_id: str
    username: str
    password_hash: str
    email: EmailStr | None = None
    created_at: datetime
