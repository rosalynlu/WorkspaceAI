from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import settings

router = APIRouter()

class GoogleLoginRequest(BaseModel):
    id_token: str

class GoogleExchangeRequest(BaseModel):
    code: str

# You must store these in .env (see below)
GOOGLE_CLIENT_ID = None
GOOGLE_CLIENT_SECRET = None
GOOGLE_REDIRECT_URI = "http://localhost:8000/auth/google/callback"


@router.post("/google/login")
def google_login(payload: GoogleLoginRequest):
    global GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_ID = getattr(settings, "GOOGLE_CLIENT_ID", None)
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Missing GOOGLE_CLIENT_ID in backend env")

    try:
        info = id_token.verify_oauth2_token(
            payload.id_token,
            grequests.Request(),
            GOOGLE_CLIENT_ID
        )
        # info contains sub, email, name, etc.
        return {"status": "ok", "email": info.get("email"), "sub": info.get("sub")}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid ID token: {str(e)}")


@router.post("/google/exchange")
def google_exchange(payload: GoogleExchangeRequest):
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", None)
    client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", None)
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Missing GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET in backend env")

    # Exchange auth code for tokens (access_token + refresh_token)
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": payload.code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": "postmessage",  # works well with GIS code client
        "grant_type": "authorization_code",
    }

    r = requests.post(token_url, data=data, timeout=30)
    if not r.ok:
        raise HTTPException(status_code=400, detail=f"Token exchange failed: {r.text}")

    tok = r.json()
    if "access_token" not in tok:
        raise HTTPException(status_code=400, detail=f"No access_token in response: {tok}")

    creds = Credentials(
        token=tok["access_token"],
        refresh_token=tok.get("refresh_token"),
        token_uri=token_url,
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/calendar.events"],
    )

    # Minimal proof: create a test event right now
    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": "WorkspaceAI Test Event",
        "start": {"dateTime": "2030-01-01T16:00:00", "timeZone": "America/Chicago"},
        "end": {"dateTime": "2030-01-01T16:30:00", "timeZone": "America/Chicago"},
    }
    created = service.events().insert(calendarId="primary", body=event).execute()

    # TODO: store refresh_token in MongoDB by user (next step once you link user identity)
    return {"status": "ok", "event_id": created.get("id")}