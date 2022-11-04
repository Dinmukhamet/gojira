import inspect
from typing import Any, Dict, Optional, Sequence, Tuple, Union, cast

from fastapi import Request
from ormar import Model, QuerySet

from gojira.constants import ALL_FIELDS
from gojira.filters.filters import FilterField, Method
from gojira.generics.meta import MetaOptions


class FilterSetMetaclass(type):
    def __new__(  # type:ignore
        cls,
        name: str,
        bases: Tuple[type, ...],
        attrs: Dict[str, Any],
        is_abstract: bool = False,
    ) -> "BaseFilterSet":
        instance = cast("BaseFilterSet", type.__new__(cls, name, bases, attrs))
        if not is_abstract:
            instance.declared_filters = {
                attr_name: attrs[attr_name]
                for attr_name, attr in attrs.items()
                if isinstance(attr, FilterField)
            }

            instance.filters = (
                instance.get_filters() | instance.declared_filters
            )

        return instance


class BaseFilterSet(metaclass=FilterSetMetaclass, is_abstract=True):
    filters: Dict[str, FilterField]
    declared_filters: Dict[str, FilterField]

    def filter_queryset(self, request: Request, queryset: QuerySet):
        for field_name, value in request.query_params.items():
            try:
                _filter = self.filters[field_name]
                value = _filter.field_class(value)
                method_name = f"filter_{field_name}"

                method: Optional[Method] = getattr(
                    self, _filter.method or method_name, None
                )
                if method is not None:
                    queryset = method(value, queryset)
                else:
                    queryset = _filter.filter(value, queryset)
            except KeyError:
                continue
        return queryset

    @classmethod
    def get_filters(cls):
        meta: Optional[MetaOptions] = getattr(cls, "Meta", None)
        assert meta is not None and inspect.isclass(meta), (
            "'%s' class must include `Meta` class" % cls.__name__
        )

        model: Optional[Model] = getattr(meta, "model", None)
        assert model is not None, (
            "%s's Meta class must define `model` attribute." % cls.__name__
        )

        fields: Optional[Union[str, Sequence[str]]] = getattr(
            meta, "fields", None
        )
        assert fields is not None, (
            "%s's Meta class must define `fields` attribute." % cls.__name__
        )

        _fields = fields
        if _fields == ALL_FIELDS:
            _fields = model.__fields__.keys()

        return {
            field_name: FilterField(
                field_class=model.__fields__.get(field_name).type_,
                field_name=field_name,
            )
            for field_name in _fields
            if field_name not in cls.declared_filters
        }
