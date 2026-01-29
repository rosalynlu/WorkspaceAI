import os
import base64
import json
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from config import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/calendar.events"
]

_creds_cache = {}


def _load_client_config():
    if os.path.exists("credentials.json"):
        with open("credentials.json", "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return payload.get("web") or payload.get("installed") or {}
    return {}


def _get_creds_from_db(user_id: str):
    from db import users_collection

    user = users_collection.find_one({"user_id": user_id})
    tokens = user.get("google_tokens") if user else None
    if not tokens:
        return None

    client = _load_client_config()
    info = {
        "token": tokens.get("token"),
        "refresh_token": tokens.get("refresh_token"),
        "token_uri": tokens.get("token_uri"),
        "client_id": tokens.get("client_id") or client.get("client_id"),
        "client_secret": tokens.get("client_secret") or client.get("client_secret"),
        "scopes": tokens.get("scopes") or SCOPES,
    }
    creds = Credentials.from_authorized_user_info(info, scopes=info["scopes"])
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        users_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "google_tokens.token": creds.token,
                    "google_tokens.expiry": creds.expiry.isoformat() if creds.expiry else None,
                }
            },
        )
    return creds


def _get_creds(user_id: str | None = None):
    if user_id:
        cached = _creds_cache.get(user_id)
        if cached is not None:
            return cached
        db_creds = _get_creds_from_db(user_id)
        if db_creds is not None:
            _creds_cache[user_id] = db_creds
            return db_creds

    if os.path.exists(settings.GOOGLE_TOKEN_JSON_PATH):
        file_creds = Credentials.from_authorized_user_file(
            settings.GOOGLE_TOKEN_JSON_PATH, scopes=SCOPES
        )
        _creds_cache["file"] = file_creds
        return file_creds

    allow_local_server = os.getenv("GOOGLE_OAUTH_LOCAL_SERVER", "").lower() in {"1", "true", "yes"}
    if allow_local_server:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        local_creds = flow.run_local_server(port=0)
        with open(settings.GOOGLE_TOKEN_JSON_PATH, "w") as token_file:
            token_file.write(local_creds.to_json())
        _creds_cache["file"] = local_creds
        return local_creds

    raise RuntimeError(
        "Missing Google OAuth token. Provide "
        f"{settings.GOOGLE_TOKEN_JSON_PATH} or set GOOGLE_OAUTH_LOCAL_SERVER=1 to run auth."
    )


# ------------------- Tools -------------------

def create_email(to: str, subject: str, body: str, user_id: str | None = None):
    service = build("gmail", "v1", credentials=_get_creds(user_id))
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {"raw": raw}
    sent = service.users().messages().send(userId="me", body=message_body).execute()
    return {"sent_to": to, "message_id": sent["id"]}


def create_doc(title: str, content: str = "", user_id: str | None = None):
    service = build("docs", "v1", credentials=_get_creds(user_id))
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    if content:
        requests = [{"insertText": {"location": {"index": 1}, "text": content}}]
        service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    return {"doc_id": doc_id, "title": title}


def create_calendar_event(summary: str, start_time: str = None, user_id: str | None = None):
    service = build("calendar", "v3", credentials=_get_creds(user_id))
    if not start_time:
        start_dt = datetime.utcnow() + timedelta(minutes=5)
    else:
        start_dt = datetime.fromisoformat(start_time)
    end_dt = start_dt + timedelta(minutes=30)
    event = {
        "summary": summary,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"}
    }
    created = service.events().insert(calendarId="primary", body=event).execute()
    return {"event_id": created["id"], "summary": summary}


def execute_tool(plan: dict, user_id: str | None = None):
    fn = plan["function_name"]
    args = plan["arguments"]

    if fn == "create_email":
        return create_email(**args, user_id=user_id)
    elif fn == "create_doc":
        return create_doc(**args, user_id=user_id)
    elif fn == "create_calendar_event":
        return create_calendar_event(**args, user_id=user_id)
    else:
        raise ValueError(f"Unknown function: {fn}")