import importlib
import logging
from functools import lru_cache
from typing import Any, Mapping, Optional, Tuple, Union

from fastapi import status
from fastapi.exceptions import HTTPException
from jose import JWTError, jwt
from ormar import NoMatch
from passlib.context import CryptContext
from pydantic import BaseConfig, create_model
from starlette.authentication import (
    AuthCredentials,
    AuthenticationBackend,
    AuthenticationError,
)
from starlette.requests import HTTPConnection

from gojira import messages
from gojira.auth.models import AbstractUser
from gojira.dependencies import DefaultSettings

logger = logging.getLogger(__file__)


@lru_cache
def get_crypt_context():
    return CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHandler:
    def __init__(self, ctx: CryptContext = get_crypt_context()) -> None:
        self.ctx = ctx

    def verify_password(self, plain_password: str, hashed_password: str):
        return self.ctx.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.ctx.hash(password)


class AnonymousUser:
    is_authenticated = False


class UserSchemaConfig(BaseConfig):
    orm_mode: bool = True


class BaseAuthentication(AuthenticationBackend):
    scheme: str = "Bearer"
    default_exception = HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )

    def __init__(
        self,
        settings: DefaultSettings,
        exception: Optional[HTTPException] = None,
        handler: PasswordHandler = PasswordHandler(),
    ):
        self.exception = exception or self.default_exception
        self.handler = handler
        self.settings = settings

    def _get_user_model(self):
        spec, model_name = self.settings.user_model.split(".")
        return getattr(importlib.import_module(spec), model_name)

    def _validate_headers(
        self, conn: HTTPConnection
    ) -> Tuple[Union[str, None], bool]:
        auth = conn.headers.get("Authorization")
        if auth is None:
            return None, False

        scheme, credentials = auth.split()
        if scheme.lower() != self.scheme.lower():
            logger.error(messages.INVALID_SCHEME, scheme, self.scheme)
            raise AuthenticationError(messages.INVALID_TOKEN)
        return credentials, True

    async def get_user(self, payload: Mapping[str, Any]) -> AbstractUser:
        claim = payload.get(self.settings.jwt_user_claim)
        if claim is None:
            logger.error(messages.USER_CLAIM_NOT_FOUND)
            raise AuthenticationError(messages.INVALID_SIGNATURE)

        filter_params = {self.settings.jwt_auth_field: claim}
        return await self.model.objects.filter(**filter_params).get()

    async def authenticate(self, conn: HTTPConnection):
        self.model: AbstractUser = self._get_user_model()
        anonymous = AuthCredentials(["authenticated"]), AnonymousUser()
        credentials, is_valid = self._validate_headers(conn)
        if not is_valid:
            return anonymous
        try:
            payload = jwt.decode(
                credentials,
                key=None,
                algorithms=[self.settings.hashing_algorithm],
                options={"verify_signature": False},
            )
            user = await self.get_user(payload)
        except JWTError as e:
            logger.error(e)
            raise AuthenticationError(messages.INVALID_TOKEN) from e
        except NoMatch as e:
            logger.error(e)
            return anonymous
        else:
            schema = self.model.get_pydantic()
            schema.Config.orm_mode = True
            UserSchema = create_model(  # type:ignore
                "UserSchema",
                is_authenticated=(bool, True),
                __base__=schema,
            )
            request_user = UserSchema.from_orm(user)
            return AuthCredentials(["authenticated"]), request_user
