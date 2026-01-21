from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    ENV: str = "dev"

    class Config:
        env_file = ".env"

settings = Settings()