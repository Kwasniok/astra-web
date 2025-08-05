from pydantic import BaseModel, Field


class JobIdsOutput(BaseModel):
    particles: list[str] = Field(description="List of particle IDs.")
    simulations: list[str] = Field(description="List of simulation IDs.")
