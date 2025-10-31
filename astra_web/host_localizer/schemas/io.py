from pydantic import BaseModel, Field


class JobNamesOutput(BaseModel):
    particles: list[str] = Field(description="List of particle names.")
    simulations: list[str] = Field(description="List of simulation names.")
