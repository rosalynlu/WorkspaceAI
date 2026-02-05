from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from config import settings

def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=getattr(settings, "JWT_EXPIRE_MINUTES", 60 * 24 * 7))
    payload = {"sub": user_id, "iat": int(now.timestamp()), "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Invalid token payload")
    return user_id