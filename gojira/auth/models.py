import ormar

from gojira.generics.models import BaseModel


class AbstractUser(BaseModel):
    class Meta(ormar.ModelMeta):
        abstract: bool = True
        tablename: str = "auth_user"

    email: str = ormar.String(max_length=255)
    password: str = ormar.String(max_length=255, nullable=True)
    is_admin: bool = ormar.Boolean(default=False)
