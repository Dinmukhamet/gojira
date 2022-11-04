from enum import Enum
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
ALL_FIELDS = "__all__"
LOOKUP_SEP = "__"
DEFAULT_LIMIT = 10
DEFAULT_OFFSET = 0


class ActionType(str, Enum):
    list = "list"
    retrieve = "retrieve"
    create = "create"
    update = "update"
    delete = "delete"
