from pydantic import BaseModel, Field


class DispatchResponse(BaseModel):

    dispatch_type: str = Field(
        description="Type of the dispatch system used, e.g., 'local' or 'slurm'."
    )

    slurm_submission: dict | None = Field(
        default=None,
        description="Submitted job data to SLURM, if applicable.",
    )
    slurm_response: dict | None = Field(
        default=None,
        description="Response from the SLURM job submission, if applicable.",
    )
