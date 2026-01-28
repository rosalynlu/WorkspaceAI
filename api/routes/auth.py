from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime
import json
import os

from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from google_auth_oauthlib.flow import Flow

from models.user import UserCreate, UserInDB
from utils.security import hash_password
from db import users_collection
from config import settings

router = APIRouter()

class GoogleTokenRequest(BaseModel):
    id_token: str

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/calendar.events",
]

DEFAULT_REDIRECT_URI = os.getenv(
    "GOOGLE_OAUTH_REDIRECT_URI", "http://localhost:8000/auth/google/callback"
)

def _load_client_config():
    candidate_paths = []
    if settings.GOOGLE_TOKEN_JSON_PATH:
        candidate_paths.append(settings.GOOGLE_TOKEN_JSON_PATH)
    candidate_paths.append(os.path.join(os.path.dirname(__file__), "..", "..", "credentials.json"))
    candidate_paths.append(os.path.join(os.getcwd(), "credentials.json"))

    for path in candidate_paths:
        try:
            if path and os.path.exists(path):
                with open(path, "r", encoding="utf-8") as handle:
                    payload = json.load(handle)
                return payload.get("web") or payload.get("installed") or {}
        except (OSError, json.JSONDecodeError):
            continue
    return {}


def _build_web_config():
    client_config = _load_client_config()
    return {
        "client_id": client_config.get("client_id") or settings.GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": client_config.get("client_secret"),
        "auth_uri": client_config.get("auth_uri") or "https://accounts.google.com/o/oauth2/auth",
        "token_uri": client_config.get("token_uri") or "https://oauth2.googleapis.com/token",
    }

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


@router.post("/google")
def verify_google_token(payload: GoogleTokenRequest):
    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GOOGLE_OAUTH_CLIENT_ID is not configured on the server",
        )

    try:
        id_info = google_id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google ID token")

    user_id = id_info.get("sub") or str(uuid4())
    email = id_info.get("email")
    existing = users_collection.find_one({"user_id": user_id})
    if not existing:
        users_collection.insert_one(
            {
                "user_id": user_id,
                "username": email or user_id,
                "password_hash": "",
                "email": email,
                "created_at": datetime.utcnow(),
                "auth_provider": "google",
                "name": id_info.get("name"),
                "picture": id_info.get("picture"),
            }
        )

    return {
        "status": "verified",
        "user_id": user_id,
        "sub": id_info.get("sub"),
        "email": email,
        "email_verified": id_info.get("email_verified"),
        "name": id_info.get("name"),
        "picture": id_info.get("picture"),
        "given_name": id_info.get("given_name"),
        "family_name": id_info.get("family_name"),
    }


@router.get("/google/authorize")
def google_authorize(user_id: str):
    web_config = _build_web_config()
    if not web_config.get("client_id") or not web_config.get("client_secret"):
        raise HTTPException(
            status_code=500,
            detail="Missing Google OAuth client credentials (client_id/client_secret)",
        )

    flow = Flow.from_client_config(
        {"web": web_config},
        scopes=SCOPES,
        redirect_uri=DEFAULT_REDIRECT_URI,
    )
    auth_url, _state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=user_id,
    )
    return {"auth_url": auth_url}


@router.get("/google/callback")
def google_callback(code: str, state: str | None = None, user_id: str | None = None):
    resolved_user_id = state or user_id
    if not resolved_user_id:
        raise HTTPException(status_code=400, detail="Missing user_id/state for Google callback")

    web_config = _build_web_config()
    if not web_config.get("client_id") or not web_config.get("client_secret"):
        raise HTTPException(
            status_code=500,
            detail="Missing Google OAuth client credentials (client_id/client_secret)",
        )

    flow = Flow.from_client_config(
        {"web": web_config},
        scopes=SCOPES,
        redirect_uri=DEFAULT_REDIRECT_URI,
    )
    try:
        flow.fetch_token(code=code)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {exc}") from exc

    creds = flow.credentials
    users_collection.update_one(
        {"user_id": resolved_user_id},
        {
            "$set": {
                "google_tokens": {
                    "token": creds.token,
                    "refresh_token": creds.refresh_token,
                    "token_uri": creds.token_uri,
                    "client_id": web_config["client_id"],
                    "client_secret": web_config["client_secret"],
                    "scopes": creds.scopes or SCOPES,
                    "expiry": creds.expiry.isoformat() if creds.expiry else None,
                }
            }
        },
        upsert=True,
    )

    return {"status": "connected", "user_id": resolved_user_id}


@router.get("/google/status")
def google_status(user_id: str):
    user = users_collection.find_one({"user_id": user_id})
    tokens = user.get("google_tokens") if user else None
    connected = bool(tokens and tokens.get("token"))
    return {"connected": connected}
