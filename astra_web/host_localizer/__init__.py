from enum import Enum
from .base import HostLocalizer
from .local import LocalHostLocalizer
from .slurm import SLURMHostLocalizer


class HostLocalizerTypes(Enum):
    LOCAL = LocalHostLocalizer
    SLURM = SLURMHostLocalizer

    @staticmethod
    def get_localizer(localizer_type: str) -> HostLocalizer:
        """
        Returns the appropriate HostLocalizer instance based on the provided type.
        """
        localizer_type = localizer_type.upper()
        if localizer_type in HostLocalizerTypes.__members__:
            return HostLocalizerTypes[localizer_type].value.instance()
        else:
            raise ValueError(f"Unknown host localizer type: {localizer_type}")
