from typing import Optional, Sequence, Union

from ormar import Model


class MetaOptions:
    model: Model
    fields: Union[str, Sequence[str]]
    exclude: Optional[Sequence[str]] = None
