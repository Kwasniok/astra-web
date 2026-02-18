from pydantic import ConfigDict
from .base import BaseConfiguration


class LocalConfiguration(BaseConfiguration):
    """
    Configuration for the local backend.
    """

    model_config = ConfigDict(extra="forbid")
