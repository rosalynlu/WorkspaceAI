import json
import os

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()  # Load .env file

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    GOOGLE_TOKEN_JSON_PATH: str = ""
    MONGODB_URL: str
    GOOGLE_OAUTH_CLIENT_ID: str = ""
    FRONTEND_ORIGINS: str = "http://localhost:5173"

    JWT_SECRET: str = "dev-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

settings = Settings()

if not settings.GOOGLE_OAUTH_CLIENT_ID:
    candidate_paths = []
    if settings.GOOGLE_TOKEN_JSON_PATH:
        candidate_paths.append(settings.GOOGLE_TOKEN_JSON_PATH)
    candidate_paths.append(os.path.join(os.path.dirname(__file__), "credentials.json"))

    for path in candidate_paths:
        if not path or not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            web_config = payload.get("web") or payload.get("installed") or {}
            client_id = web_config.get("client_id")
            if client_id:
                settings.GOOGLE_OAUTH_CLIENT_ID = client_id
                break
        except (OSError, json.JSONDecodeError):
            continue