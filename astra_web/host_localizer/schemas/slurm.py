import os
from pydantic import BaseModel, Field, computed_field
from slurm_requests import SLURMJobState


class SLURMConfiguration(BaseModel):
    """
    Configuration for the SLURM backend.
    """

    astra_binary_path: str
    data_path: str
    output_path: str
    base_url: str
    api_version: str
    proxy_url: str | None = None
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


class SLURMJobOutput(BaseModel):
    id: int = Field(description="The ID of the SLURM job.")
    partition: str | None = Field(description="The partition of the SLURM job.")
    name: str = Field(description="Full name of the SLURM job.")
    state_current: list[SLURMJobState] = Field(
        description="The current state of the SLURM job."
    )
    state_reason: str = Field(
        description="The reason for the current state of the SLURM job."
    )


class SLURMDispatchedJobOutput(BaseModel):
    """SLURM job information."""

    id: str = Field(
        description="ID of the dispatched task. (Not the SLURM job ID or name.)"
    )
    slurm: SLURMJobOutput = Field(description="SLURM job state information.")


class SLURMDispatchedJobsOutput(BaseModel):
    """SLURM dispatched jobs."""

    particles: list[SLURMDispatchedJobOutput] = Field(
        description="List of dispatched generator SLURM jobs."
    )
    simulations: list[SLURMDispatchedJobOutput] = Field(
        description="List of dispatched simulation SLURM jobs."
    )


class SLURMDispatchedIDsOutput(BaseModel):
    """SLURM dispatched IDs."""

    particles: list[str] = Field(
        description="List of dispatched generator SLURM job dispatch IDs."
    )
    simulations: list[str] = Field(
        description="List of dispatched simulation SLURM job dispatch IDs."
    )
