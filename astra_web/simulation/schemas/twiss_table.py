from astra_web.schemas.table import Table
from pydantic import ConfigDict, Field


class TwissTable(Table):
    """Transversal Twiss parameter table for x or y dimension."""

    model_config = ConfigDict(extra="forbid")

    alpha_x: list[float] = Field(
        description="alpha parameter for x dimension.",
    )
    beta_x: list[float] = Field(
        description="beta parameter for x dimension.",
    )
    gamma_x: list[float] = Field(
        description="gamma parameter for x dimension.",
    )
    alpha_y: list[float] = Field(
        description="alpha parameter for y dimension.",
    )
    beta_y: list[float] = Field(
        description="beta parameter for y dimension.",
    )
    gamma_y: list[float] = Field(
        description="gamma parameter for y dimension.",
    )
