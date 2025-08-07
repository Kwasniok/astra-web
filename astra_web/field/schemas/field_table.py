from astra_web.schemas.table import Table
from pydantic import ConfigDict, Field


class FieldTable(Table):
    model_config = ConfigDict(extra="forbid")

    z: list[float] = Field(
        description="Longitudinal z-positions of the field.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    v: list[float] = Field(
        description="Field values at the corresponding z positions.",
        json_schema_extra={"format": "Unit: [free]"},
    )
