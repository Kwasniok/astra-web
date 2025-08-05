from enum import Enum


class ListCategory(Enum):
    """Enumeration of all available listing categories."""

    ALL = "all"
    FINISHED = "finished"
    PENDING = "pending"
