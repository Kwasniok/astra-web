from enum import Enum


class DispatchStatus(Enum):

    FAILED = "failed"
    FINISHED = "finished"
    UNFINISHED = "unfinished"
