from fastapi import APIRouter, HTTPException
from uuid import uuid4
from datetime import datetime

from models.user import UserCreate, UserInDB
from utils.security import hash_password
from db import users_collection

router = APIRouter()

@router.post("/register")
def register_user(user: UserCreate):
    existing = users_collection.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user_id = str(uuid4())

    user_in_db = UserInDB(
        user_id=user_id,
        username=user.username,
        password_hash=hash_password(user.password),
        email=user.email,
        created_at=datetime.utcnow(),
    )

    users_collection.insert_one(user_in_db.model_dump())

    return {"status": "registered", "user_id": user_id}
