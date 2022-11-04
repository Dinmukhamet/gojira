from typing import List, Type

from fastapi import Request, Response, status
from ormar import Model, QuerySet
from pydantic import BaseModel

from gojira.constants import DEFAULT_LIMIT, DEFAULT_OFFSET
from gojira.filters.backends import FilterBackend


class CreateMixin:
    async def create(self, request: Request, response: Response):
        raw_data = await request.json()
        queryset: QuerySet = self.get_queryset()  # type:ignore
        instance: Model = await queryset.create(**raw_data)
        response.status_code = status.HTTP_201_CREATED
        return instance


class LimitOffsetPagination(BaseModel):
    limit: int = DEFAULT_LIMIT
    offset: int = DEFAULT_OFFSET


class ListMixin:
    filter_backends: List[Type[FilterBackend]] = []

    def filter_queryset(
        self, request: Request, queryset: QuerySet
    ) -> QuerySet:
        for backend_cls in self.filter_backends:
            backend: FilterBackend = backend_cls()
            queryset = backend.filter_queryset(request, queryset, self)
        return queryset

    def paginate_queryset(self, request: Request, queryset: QuerySet):
        pagination = LimitOffsetPagination(**request.query_params)
        return queryset.limit(pagination.limit).offset(pagination.offset)

    async def list(self, request: Request):
        queryset: QuerySet = self.filter_queryset(
            request=request, queryset=self.get_queryset()  # type:ignore
        )
        paginated = self.paginate_queryset(request, queryset)
        if paginated is not None:
            return {
                "count": await queryset.count(),
                "data": await paginated.all(),
            }
        return await queryset.all()


class RetrieveMixin:
    async def retrieve(self, request: Request):
        instance: Model = await self.get_object(request=request)  # type:ignore
        return instance


class UpdateMixin:
    async def update(self, request: Request):
        instance: Model = await self.get_object(request=request)  # type:ignore
        raw_data = await request.json()
        return await instance.update(**raw_data)


class DestroyMixin:
    async def delete(self, request: Request):
        instance: Model = await self.get_object(request=request)  # type:ignore
        return await instance.delete()
