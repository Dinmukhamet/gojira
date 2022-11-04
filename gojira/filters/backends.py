from typing import Optional, Type

from fastapi import Request
from ormar import QuerySet

from gojira.filters.filterset import BaseFilterSet


class FilterBackend:
    def get_filterset_class(self, view) -> Optional[Type[BaseFilterSet]]:
        return getattr(view, "filterset_class", None)

    def filter_queryset(self, request: Request, queryset: QuerySet, view):
        filterset_class = self.get_filterset_class(view)
        if filterset_class is not None:
            filterset = filterset_class()
            return filterset.filter_queryset(request, queryset)
        return queryset
