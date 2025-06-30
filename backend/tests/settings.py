# tests/settings.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    PAIC_CONFIG_PATH: str
    PAIC_CONFIG_BRANCH_NAME: str

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        case_sensitive = True
        extra = "allow"

settings = Settings()