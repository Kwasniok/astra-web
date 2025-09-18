from astra_web.schemas.table import Table
from pydantic import ConfigDict, Field


class XEmittanceTable(Table):
    model_config = ConfigDict(extra="forbid")

    z: list[float] = Field(
        description="Longitudinal positions.", json_schema_extra={"format": "Unit: [m]"}
    )
    t: list[float] = Field(
        description="Time points", json_schema_extra={"format": "Unit: [ns]"}
    )
    mean: list[float] = Field(
        description="Average transverse position in x or y direction.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    position_rms: list[float] = Field(
        description="RMS deviation in x or y direction.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    angle_rms: list[float] = Field(
        description="RMS inclination angle deviation in x or y direction.",
        json_schema_extra={"format": "Unit: [mrad]"},
    )
    emittance: list[float] = Field(
        description="Normed emittance in x or y direction.",
        json_schema_extra={"format": "Unit: [pi*mrad*mm]"},
    )
    correlation: list[float] = Field(
        description="Correlation of position coordinates and momenta in x or y direction.",
        json_schema_extra={"format": "Unit: [mrad]"},
    )


class ZEmittanceTable(Table):
    model_config = ConfigDict(extra="forbid")

    z: list[float] = Field(
        description="Longitudinal positions.", json_schema_extra={"format": "Unit: [m]"}
    )
    t: list[float] = Field(
        description="Time points", json_schema_extra={"format": "Unit: [ns]"}
    )
    E_kin: list[float] = Field(
        description="Average transverse position in x or y direction.",
        json_schema_extra={"format": "Unit: [MeV]"},
    )
    position_rms: list[float] = Field(
        description="RMS deviation in x or y direction.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    delta_E_rms: list[float] = Field(
        description="RMS inclination angle deviation in x or y direction.",
        json_schema_extra={"format": "Unit: [keV]"},
    )
    emittance: list[float] = Field(
        description="Normed emittance in x or y direction.",
        json_schema_extra={"format": "Unit: [pi*keV*mm]"},
    )
    correlation: list[float] = Field(
        description="Correlation of position coordinates and mean energy in x or y direction.",
        json_schema_extra={"format": "Unit: [keV]"},
    )
