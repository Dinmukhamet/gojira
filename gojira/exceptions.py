from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from gojira import messages


class APIException(HTTPException):
    status_code: int
    details: str

    def __init__(self, headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(self.status_code, self.details, headers)


class PermissionDeniedException(APIException):
    status_code: int = status.HTTP_403_FORBIDDEN
    details: str = messages.PERMISSION_DENIED
