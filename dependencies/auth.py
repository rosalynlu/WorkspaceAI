from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from db import users_collection
from utils.jwt import decode_access_token

bearer = HTTPBearer(auto_error=False)

def get_current_user_id(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    try:
        user_id = decode_access_token(creds.credentials)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user_id