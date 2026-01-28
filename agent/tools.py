import os
import base64
from email.mime.text import MIMEText
from datetime import datetime, timedelta

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from config import settings

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/calendar.events"
]

_creds = None


def _get_creds():
    global _creds
    if _creds is not None:
        return _creds

    if os.path.exists(settings.GOOGLE_TOKEN_JSON_PATH):
        _creds = Credentials.from_authorized_user_file(
            settings.GOOGLE_TOKEN_JSON_PATH, scopes=SCOPES
        )
        return _creds

    allow_local_server = os.getenv("GOOGLE_OAUTH_LOCAL_SERVER", "").lower() in {"1", "true", "yes"}
    if allow_local_server:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        _creds = flow.run_local_server(port=0)
        with open(settings.GOOGLE_TOKEN_JSON_PATH, "w") as token_file:
            token_file.write(_creds.to_json())
        return _creds

    raise RuntimeError(
        "Missing Google OAuth token. Provide "
        f"{settings.GOOGLE_TOKEN_JSON_PATH} or set GOOGLE_OAUTH_LOCAL_SERVER=1 to run auth."
    )


# ------------------- Tools -------------------

def create_email(to: str, subject: str, body: str):
    service = build("gmail", "v1", credentials=_get_creds())
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    message_body = {"raw": raw}
    sent = service.users().messages().send(userId="me", body=message_body).execute()
    return {"sent_to": to, "message_id": sent["id"]}


def create_doc(title: str, content: str = ""):
    service = build("docs", "v1", credentials=_get_creds())
    doc = service.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    if content:
        requests = [{"insertText": {"location": {"index": 1}, "text": content}}]
        service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    return {"doc_id": doc_id, "title": title}


def create_calendar_event(summary: str, start_time: str = None):
    service = build("calendar", "v3", credentials=_get_creds())
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


def execute_tool(plan: dict):
    fn = plan["function_name"]
    args = plan["arguments"]

    if fn == "create_email":
        return create_email(**args)
    elif fn == "create_doc":
        return create_doc(**args)
    elif fn == "create_calendar_event":
        return create_calendar_event(**args)
    else:
        raise ValueError(f"Unknown function: {fn}")