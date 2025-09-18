from astra_web.schemas.table import Table
from pydantic import ConfigDict, Field


class Transversal1DNormalizedEmittanceTable(Table):
    """Transversal emittance table for x or y dimension."""

    model_config = ConfigDict(extra="forbid")

    z: list[float] = Field(
        description="Longitudinal position.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    t: list[float] = Field(
        description="Time point.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    position_mean: list[float] = Field(
        description="Average transverse position.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    position_rms: list[float] = Field(
        description="RMS of transverse position.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    angle_rms: list[float] = Field(
        description="RMS of transverse inclination angle.",
        json_schema_extra={"format": "Unit: [mrad]"},
    )
    emittance_normalized: list[float] = Field(
        description="Normalized transversal emittance.",
        json_schema_extra={"format": "Unit: [π*mrad*mm]"},
    )
    correlation: list[float] = Field(
        description="Transverse correlation of position coordinates and angle. E.g. for x-axis: `mean(x * x')`.",
        json_schema_extra={"format": "Unit: [mrad]"},
    )


class LongitudinalNormalizedEmittanceTable(Table):
    """Longitudinal emittance table for z dimension."""

    model_config = ConfigDict(extra="forbid")

    z: list[float] = Field(
        description="Longitudinal position.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    t: list[float] = Field(
        description="Time point.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    E_kin: list[float] = Field(
        description="Average kinetic energy.",
        json_schema_extra={"format": "Unit: [MeV]"},
    )
    position_rms: list[float] = Field(
        description="RMS of longitudinal position.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    energy_spread_rms: list[float] = Field(
        description="RMS energy spread.",
        json_schema_extra={"format": "Unit: [keV]"},
    )
    emittance_normalized: list[float] = Field(
        description="Normalized longitudinal emittance.",
        json_schema_extra={"format": "Unit: [π*keV*mm]"},
    )
    correlation: list[float] = Field(
        description="Longitudinal correlation of position and relative energy deviation - `mean(z * E')`.",
        json_schema_extra={"format": "Unit: [keV]"},
    )


class TraceSpaceEmittanceTable(Table):
    """Trace space emittance table."""

    model_config = ConfigDict(extra="forbid")

    z: list[float] = Field(
        description="Longitudinal position.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    t: list[float] = Field(
        description="Time point.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    emittance_trace_space_rms_x: list[float] = Field(
        description="RMS strace space emittance in x direction.",
        json_schema_extra={"format": "Unit: [π mrad mm]"},
    )
    emittance_trace_space_rms_y: list[float] = Field(
        description="RMS strace space emittance in y direction.",
        json_schema_extra={"format": "Unit: [π mrad mm]"},
    )
    emittance_trace_space_rms_z: list[float] = Field(
        description="RMS strace space emittance in z direction.",
        json_schema_extra={"format": "Unit: [π µm]"},
    )
