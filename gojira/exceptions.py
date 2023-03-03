from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from gojira import messages


class APIException(HTTPException):
    status_code: int
    detail: str

    def __init__(self, headers: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(
            status_code=self.status_code, detail=self.detail, headers=headers
        )


class PermissionDeniedException(APIException):
    status_code: int = status.HTTP_403_FORBIDDEN
    detail: str = messages.PERMISSION_DENIED
