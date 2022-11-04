from dataclasses import dataclass
from typing import Any, Dict, List, Set, Tuple

from fastapi import status

from gojira.constants import ALL_FIELDS
from gojira.generics.exceptions import SerializerValidationError
from gojira.generics.meta import MetaOptions
from gojira.messages import NO_FIELDS_TO_DISPLAY


@dataclass
class Field:
    source: str
    read_only: bool = False


class MethodField(Field):
    pass


class SerializerMeta(type):
    Meta: MetaOptions
    _fields: Set[str]

    def __new__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        namespace: Dict[str, Any],
        is_abstract: bool = False,
    ) -> type:
        instance = type.__new__(cls, name, bases, namespace)
        if not is_abstract:
            assert (
                hasattr(instance.Meta, "model")
                and instance.Meta.model is not None
            ), ("%s's Meta class must have `model` attribute.") % cls.__name__
            assert (
                hasattr(instance.Meta, "fields")
                or instance.Meta.fields is not None
            ), ("%s's Meta class must have `fields` attribute." % cls.__name__)

            fields: List[str] = list()

            if (
                isinstance(instance.Meta.fields, str)
                and instance.Meta.fields == ALL_FIELDS
            ):
                fields = list(instance.Meta.model.__fields__.keys())
            else:
                fields = list(instance.Meta.fields)

            if (
                hasattr(instance.Meta, "exclude")
                and instance.Meta.exclude is not None
            ):
                for field in instance.Meta.exclude:
                    try:
                        fields.remove(field)
                    except ValueError:
                        continue

            if not fields:
                raise SerializerValidationError(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=NO_FIELDS_TO_DISPLAY % cls.__name__,
                )

            instance._fields = set(fields)
        return instance


class ModelSerializer(metaclass=SerializerMeta, is_abstract=True):
    pass
