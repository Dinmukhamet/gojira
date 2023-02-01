import logging
import uuid
from dataclasses import dataclass
from datetime import date
from enum import Enum
from functools import wraps
from typing import Any, Dict, List, Mapping, Optional, Tuple, Type, cast

import pydantic
from classy_fastapi import Routable
from classy_fastapi.routable import RoutableMeta
from classy_fastapi.route_args import EndpointDefinition, RouteArgs
from fastapi import APIRouter, HTTPException, Request, status
from ormar import Model, QuerySet
from starlette.convertors import Convertor, register_url_convertor

from gojira import permissions
from gojira.generics.serializers import ModelSerializer

logger = logging.getLogger(__file__)


class ControllerMeta(RoutableMeta):
    @classmethod
    def __get_app_name(cls, model_cls) -> Optional[str]:
        try:
            return model_cls.Meta.tablename.split("_")[0]
        except Exception:
            return "default"

    def __new__(  # type:ignore
        cls,
        name: str,
        bases: Tuple[Type[Any]],
        attrs: Dict[str, Any],
    ) -> "GenericController":
        instance = cast(
            "GenericController", super().__new__(cls, name, bases, attrs)
        )
        endpoints: List[EndpointDefinition] = attrs["_endpoints"]

        model_cls = attrs.get("model")

        if model_cls is not None:
            for method in Method:
                try:
                    api_method: APIMethod = method.value
                    endpoint = getattr(instance, api_method.method_name)
                except AttributeError as e:
                    pass
                else:
                    serializer_cls = instance.get_serializer_class(
                        api_method.method_name
                    )
                    include = getattr(serializer_cls, "_fields", None)

                    model = model_cls.get_pydantic(include=include)

                    lookup_type = model_cls.__fields__.get(
                        instance.lookup_field
                    ).type_.__name__

                    path = construct_path(
                        method=method,
                        prefix=instance.prefix,
                        lookup=f"{instance.lookup_field}:{lookup_type}",
                    )

                    name = "%s_%s" % (api_method.method_name, instance.prefix)
                    if api_method.name == "PATCH":
                        name = "partial_" + name
                    setattr(endpoint, "__name__", name)
                    app_name = cls.__get_app_name(model_cls)

                    openapi_extra = {
                        "tags": [app_name],
                    }

                    if api_method.name in ("POST", "PUT"):
                        openapi_extra.update(
                            {
                                "requestBody": {
                                    "content": {
                                        "application/json": {
                                            "schema": model.schema()
                                        }
                                    },
                                    "required": True,
                                }
                            }
                        )

                    if api_method.method_name in (
                        "retrieve",
                        "update",
                        "delete",
                    ):
                        openapi_extra.update(
                            {
                                "parameters": [
                                    {
                                        "in": "path",
                                        "name": instance.lookup_field,
                                    }
                                ]
                            }
                        )

                    endpoints.append(
                        EndpointDefinition(
                            endpoint=endpoint,
                            args=RouteArgs(
                                path=path,
                                methods={api_method.name},
                                name=name,
                                response_model=model
                                if api_method.method_name != "list"
                                else get_paginated_response(
                                    model  # type:ignore
                                ),
                                response_model_exclude=getattr(
                                    serializer_cls, "exclude", None
                                ),
                                openapi_extra=openapi_extra,
                            ),
                        )
                    )
        return instance


class BaseController(Routable, metaclass=ControllerMeta):
    prefix: str

    async def get_object(self, request: Request) -> Model:
        raise NotImplementedError(
            "%s must implement `get_object()` method" % self.__class__.__name__
        )

    def get_queryset(self) -> QuerySet:
        raise NotImplementedError(
            "%s must implement `get_queryset()` method"
            % self.__class__.__name__
        )

    def get_serializer_class(
        self, action: str
    ) -> Optional[Type[ModelSerializer]]:
        raise NotImplementedError(
            "%s must implement `get_serializer_class()` method"
            % self.__class__.__name__
        )


@dataclass
class APIMethod:
    name: str
    method_name: str


class Method(Enum):
    LIST = APIMethod(name="GET", method_name="list")
    RETRIEVE = APIMethod(name="GET", method_name="retrieve")
    CREATE = APIMethod(name="POST", method_name="create")
    PUT = APIMethod(name="PUT", method_name="update")
    PATCH = APIMethod(name="PATCH", method_name="update")
    DELETE = APIMethod(name="DELETE", method_name="delete")


def construct_path(method, prefix: str, lookup: str):
    base = "/%s/" % prefix
    if method in (Method.LIST, Method.CREATE):
        return base
    return f"{base}{{{lookup}}}/"


def get_paginated_response(model: Model):
    def validate_data(cls, model):
        return model

    validators = {
        "data_validator": pydantic.validator("data", allow_reuse=True)(
            validate_data
        )
    }
    return pydantic.create_model(
        "PaginatedResponse_" + uuid.uuid4().hex.upper()[0:6],
        count=(int, 0),
        data=(List[model], ...),  # type:ignore
        __validators__=validators,
    )


class GenericController(BaseController):
    prefix: str = ""
    model: Type[Model]
    serializer_map: Mapping[str, Type[ModelSerializer]]
    permission_classes: Tuple[Type[permissions.BasePermission], ...] = (
        permissions.AllowAny,
    )
    _endpoints: List[EndpointDefinition] = []
    lookup_field: str = "id"

    async def get_object(self, request: Request):
        queryset: QuerySet = self.get_queryset()
        lookup = request.path_params.get(self.lookup_field)

        if lookup is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{self.lookup_field} was not found in path params",
            )

        filter_kwargs = {self.lookup_field: lookup}

        instance: Optional[Model] = await queryset.get_or_none(
            **filter_kwargs
        )  # type:ignore
        if instance is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "%s with %s: %s does not exist"
                    % instance.__class__.__name__,
                    self.lookup_field,
                    lookup,
                ),
            )

        return instance

    def get_queryset(self):
        assert self.model is not None, (
            "'%s' should either include a `model` attribute, "
            "or override `get_queryset()` method." % self.__class__.__name__
        )
        return self.model.objects

    @classmethod
    def get_serializer_map(cls):
        assert (
            hasattr(cls, "serializer_map") and cls.serializer_map is not None
        ), (
            "'%s' shoud either include a `serializer_map` attribute, "
            "or override `get_queryset()` method." % cls.__name__
        )
        return cls.serializer_map

    @classmethod
    def get_serializer_class(
        cls, action: str
    ) -> Optional[Type[ModelSerializer]]:
        serializers = cls.get_serializer_map()
        return serializers.get(action)


class DateConvertor(Convertor):
    regex = "[0-9]{4}-[0-9]{2}-[0-9]{2}"

    def convert(self, value: str) -> date:
        return date.fromisoformat(value)

    def to_string(self, value: date) -> str:
        return value.isoformat()


class GenericRouter:
    def __init__(self, router: APIRouter):
        self.router = router

    def register(self, view_cls, path: Optional[str] = None):
        @wraps(view_cls)  # type:ignore
        def decorated(*args, **kwargs):
            result = view_cls(*args, **kwargs)
            return result

        register_url_convertor("date", DateConvertor())
        view: GenericController = decorated()

        if path is not None:
            for route in view.router.routes:
                route.path = path  # type:ignore
        return self.router.include_router(view.router)
