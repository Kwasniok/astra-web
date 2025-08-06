import os
from pydantic import BaseModel, computed_field


class SLURMConfiguration(BaseModel):
    """
    Configuration for the SLURM backend.
    """

    astra_binary_path: str
    data_path: str
    output_path: str = "."
    base_url: str
    api_version: str
    proxy: str | None = None
    user_name: str
    user_token: str
    partition: str
    constraints: str | None = None
    environment: list[str] = []
    script_setup: str = ""

    @computed_field
    @property
    def generator_data_path(self) -> str:
        return os.path.join(self.data_path, "generator")

    @computed_field
    @property
    def simulation_data_path(self) -> str:
        return os.path.join(self.data_path, "simulation")
