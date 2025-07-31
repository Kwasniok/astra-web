from enum import Enum
from .base import HostLocalizer
from .local import LocalHostLocalizer
from .slurm import SLURMHostLocalizer


class Hosts(Enum):
    """Enumeration of all available host names."""

    LOCAL = "local"
    SLURM = "slurm"


class HostLocalizerTypes(Enum):
    """Enumeration of all available host localizer types."""

    # LocalHostLocalizer is used for local development and
    LOCAL = LocalHostLocalizer
    SLURM = SLURMHostLocalizer

    @staticmethod
    def get_localizer(host: Hosts) -> HostLocalizer:
        """
        Returns the appropriate HostLocalizer instance based on the provided type.
        """
        localizer_type = host.value.upper()
        if localizer_type in HostLocalizerTypes.__members__:
            return HostLocalizerTypes[localizer_type].value.instance()
        else:
            raise ValueError(f"Unknown host localizer type: {localizer_type}")
