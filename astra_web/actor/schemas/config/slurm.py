from pydantic import ConfigDict, Field
from .base import BaseConfiguration


class SLURMConfiguration(BaseConfiguration):
    """
    Configuration for the SLURM backend.
    """

    model_config = ConfigDict(extra="forbid")

    base_url: str = Field(
        ...,
        description="Base URL of the SLURM API excluding endpoints.",
        example="https://slurm-rest.example.com/sapi",
    )
    api_version: str = Field(
        ...,
        description="Version of the SLURM API to use.",
        example="v0.0.40",
    )
    proxy_url: str | None = Field(
        default=None,
        description="URL of the proxy to use for SLURM API requests, if any.",
        example="socks5://localhost:8080",
    )
    user_name: str = Field(
        ...,
        description="Username to authenticate with the SLURM API.",
        example="john_doe",
    )
    user_token: str = Field(
        ...,
        description="Token to authenticate with the SLURM API.",
        example="your_token_here",
    )
    partition: str | None = Field(
        default=None,
        description="Partition to submit jobs to.",
        example="default",
    )
    nice: int | None = Field(
        default=None,
        description="Nice value for the job.",
        example=0,
    )
    constraints: str | None = Field(
        default=None,
        description="Constraints for the job.",
        example="gpu",
    )
    environment: list[str] = Field(
        default_factory=list,
        description="Environment variables for the job.",
        example=["PATH=/bin:/usr/bin/:/usr/local/bin/", "MORE=values"],
    )
    job_output_path: str = Field(
        ...,
        description="Path to store SLURM job output.",
        example="/tmp/slurm",
    )
    job_setup: str = Field(
        default="",
        description="Setup BASH fragment for the job.",
        example="module purge\nmodule load openmpi",
    )
    data_path: str | None = Field(
        default=None,
        description="Optional: Path to data directory as seen by the SLURM cluster.",
    )
    astra_binary_path: str | None = Field(
        default=None,
        description="Optional: Path to the ASTRA binaries directory as seen by the SLURM cluster.",
    )
