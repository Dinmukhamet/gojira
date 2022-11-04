from datetime import datetime

import ormar

from gojira.dependencies import get_metadata


class BaseModel(ormar.Model):
    class Meta(ormar.ModelMeta):
        abstract = True
        metadata = get_metadata()
        extra = (
            ormar.Extra.ignore
        )  # set extra setting to prevent exceptions on extra fields presence

    id: int = ormar.BigInteger(primary_key=True)
    created_at: datetime = ormar.DateTime(default=datetime.now())
