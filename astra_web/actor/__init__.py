from enum import Enum
from .base import Actor
from .local import LocalActor
from .slurm import SLURMActor
from .schemas.config import BaseConfiguration, LocalConfiguration, SLURMConfiguration


class Actors(Enum):
    """Enumeration of all available host names."""

    LOCAL = "local"
    SLURM = "slurm"


ActorConfigurations = LocalConfiguration | SLURMConfiguration


class ActorTypes(Enum):
    """Enumeration of all available host actor types."""

    LOCAL = LocalActor, LocalConfiguration
    SLURM = SLURMActor, SLURMConfiguration

    @staticmethod
    def init(host: Actors, config: ActorConfigurations | None = None) -> Actor:
        """
        Returns the appropriate Actor instance based on the provided type.

        Raises:
            ValueError: If the provided host type is unknown or if the configuration type is invalid.
        """
        actor_type = host.value.upper()

        if actor_type not in ActorTypes.__members__:
            raise ValueError(f"Unknown host actor type: {actor_type}")

        cls = ActorTypes[actor_type].value[0]
        config_cls = ActorTypes[actor_type].value[1]

        if config is None:
            try:
                config = config_cls()  # type: ignore
            except Exception as e:
                raise ValueError(
                    f"Failed to default initialize configuration for {actor_type} actor: {e}"
                )

        if not isinstance(config, config_cls):
            raise ValueError(
                f"Invalid configuration type for {actor_type} actor. "
                f"Expected {config_cls.__name__}, got {type(config).__name__}."
            )

        return cls(config)  # type: ignore
