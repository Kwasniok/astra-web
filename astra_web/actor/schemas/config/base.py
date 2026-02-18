import os
from pydantic import BaseModel, ConfigDict


class BaseConfiguration(BaseModel):
    """
    Base for configuration for the backend.
    """

    model_config = ConfigDict(extra="forbid")

    def __init__(self, **data):
        super().__init__(**data)
        self._data_path = os.environ["ASTRA_DATA_PATH"]
        self._astra_binary_path = os.environ["ASTRA_BINARY_PATH"]
