from fastapi import HTTPException


class SerializerValidationError(HTTPException):
    pass
