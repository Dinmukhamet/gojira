from typing import Any, Optional, Type

from ormar import QuerySet

from gojira.constants import LOOKUP_SEP

DEFAULT_LOOKUP = "exact"


class Method:
    def __call__(self, value: Any, queryset: QuerySet) -> QuerySet:
        pass


class FilterField:
    def __init__(
        self,
        field_class: Type,
        field_name: Optional[str] = None,
        lookup_expr: str = DEFAULT_LOOKUP,
        method: Optional[str] = None,
    ):
        self.field_class = field_class
        self.field_name = field_name
        self.lookup_expr = lookup_expr
        self.method = method

    def get_filter_name(self):
        return LOOKUP_SEP.join([self.field_name, self.lookup_expr])

    def filter(self, value: Any, queryset: QuerySet):
        filter_name = self.get_filter_name()
        parameters = {filter_name: self.field_class(value)}
        return queryset.filter(**parameters)


class StringFilter(FilterField):
    def __init__(
        self,
        field_name: Optional[str] = None,
        method: Optional[str] = None,
    ):
        super().__init__(field_class=str, field_name=field_name, method=method)


class IntegerFilter(FilterField):
    def __init__(
        self,
        field_name: Optional[str] = None,
        method: Optional[str] = None,
    ):
        super().__init__(field_class=int, field_name=field_name, method=method)
