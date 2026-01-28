from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()  # Load .env file

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    GOOGLE_TOKEN_JSON_PATH: str
    MONGODB_URL: str

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None

settings = Settings()