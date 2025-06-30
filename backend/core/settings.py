# core/settings.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    # Frontend
    FRONTEND_ORIGIN: str
    FRONTEND_BUILD_DIR: str
    UVICORN_MODE: str

    # Database & user
    USER_FILE: str
    DATABASE_FOLDER: str
    DATABASE_URL: str

    # Token
    TOKEN_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ACCESS_TOKEN_SECRET_KEY: str
    REFRESH_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_SECRET_KEY: str

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()