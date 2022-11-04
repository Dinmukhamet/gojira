from functools import lru_cache

from pydantic import BaseSettings
from sqlalchemy import MetaData


class DefaultSettings(BaseSettings):
    secret_key: str
    database_url: str
    hashing_algorithm: str
    jwt_auth_field: str = "email"
    jwt_user_claim: str = "sub"
    debug: bool = False
    user_model: str = "auth.CustomUser"


@lru_cache()
def get_metadata():
    return MetaData()
