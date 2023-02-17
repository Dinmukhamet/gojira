from functools import reduce
from typing import Any, Dict, Iterable, Sequence, Tuple, Type

from fastapi import Request


class PermissionOperator:
    def __init__(self, *permission_classes: Type["BasePermission"]):
        self.permission_classes = permission_classes


class or_(PermissionOperator):
    async def __call__(self, request: Request) -> bool:
        self.request = request

        for permission_class in self.permission_classes:
            permission = permission_class()
            if await permission(request=request):
                return True

        return False


class and_(PermissionOperator):
    async def __call__(self, request: Request) -> bool:
        self.request = request

        for permission_class in self.permission_classes:
            permission = permission_class()
            if not await permission(request=request):
                return False

        return True


class PermissionMeta(type):
    @classmethod
    def __or__(cls, other: "PermissionMeta"):
        return or_((cls, other))


class BasePermission(metaclass=PermissionMeta):
    async def __call__(self, request: Request) -> bool:
        try:
            self.request = request
            return await self.has_permission()
        except Exception:
            return False

    async def has_permission(self) -> bool:
        raise NotImplementedError()


class IsAuthenticated(BasePermission):
    async def has_permission(self) -> bool:
        return self.request.user.is_authenticated


SAFE_METHODS = ["GET", "HEAD", "OPTIONS"]


class IsAuthenticatedOrReadOnly(BasePermission):
    async def has_permission(self) -> bool:
        if not self.request.method in SAFE_METHODS:
            return self.request.user.is_authenticated
        return True


class IsAdmin(BasePermission):
    async def has_permission(self) -> bool:
        return self.request.user.is_admin


class AllowAny(BasePermission):
    async def has_permission(self) -> bool:
        return True
