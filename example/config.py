from functools import lru_cache
from pathlib import Path

from databases import Database

from gojira.dependencies import DefaultSettings

BASE_DIR = Path(__file__).resolve().parent


class Settings(DefaultSettings):
    user_model: str = "my_auth.CustomUser"

    class Config:
        env_file = BASE_DIR / ".env"


@lru_cache
def get_settings():
    return Settings()


@lru_cache
def get_database():
    settings = get_settings()
    return Database(settings.database_url)
