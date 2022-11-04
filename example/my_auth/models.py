import ormar

from example.config import get_database
from gojira.auth.models import AbstractUser


class CustomUser(AbstractUser):
    full_name: str = ormar.String(max_length=255)

    class Meta:
        tablename = "auth_user"
        database = get_database()
