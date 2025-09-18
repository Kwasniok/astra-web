from astra_web.schemas.table import Table
from pydantic import ConfigDict, Field


class CavityAutoPhaseTable(Table):
    """Cavity auto phase table."""

    model_config = ConfigDict(extra="forbid")

    energy_gain: list[float] = Field(
        description="Energy gain.",
        json_schema_extra={"format": "Unit: [MeV]"},
    )
    absolute_phase: list[float] = Field(
        description="Absolute cavity phase.",
        json_schema_extra={"format": "Unit: [deg]"},
    )
