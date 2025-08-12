from enum import Enum


class DispatchStatus(Enum):

    ANY = "any"
    FAILED = "failed"
    FINISHED = "finished"
    PENDING = "pending"
