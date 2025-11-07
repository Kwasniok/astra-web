from enum import Enum
from .base import Actor
from .local import LocalActor
from .slurm import SLURMActor


class Actors(Enum):
    """Enumeration of all available host names."""

    LOCAL = "local"
    SLURM = "slurm"


class ActorTypes(Enum):
    """Enumeration of all available host actor types."""

    LOCAL = LocalActor
    SLURM = SLURMActor

    @staticmethod
    def select(host: Actors) -> Actor:
        """
        Returns the appropriate Actor instance based on the provided type.
        """
        actor_type = host.value.upper()
        if actor_type in ActorTypes.__members__:
            return ActorTypes[actor_type].value.instance()
        else:
            raise ValueError(f"Unknown host actor type: {actor_type}")
