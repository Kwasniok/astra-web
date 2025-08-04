from pydantic import BaseModel, ConfigDict, Field
from typing import Type, TypeVar
from astra_web.file import write_csv, read_csv

T = TypeVar("T", bound="Parent")


class Table(BaseModel):
    model_config = ConfigDict(extra="forbid")

    def write_to_csv(self, path: str) -> None:
        """
        Write the table data to a CSV file.
        """
        write_csv(self, path)

    @classmethod
    def load_from_csv(cls: Type[T], path: str) -> T:
        """
        Load the table data from a CSV file.
        """
        return read_csv(cls, path)


class FieldTable(Table):
    model_config = ConfigDict(extra="forbid")

    z: list[float] = Field(
        description="Longitudinal positions along z-axis.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    v: list[float] = Field(
        description="Field values at z positions in free units.",
        json_schema_extra={"format": "Unit: free"},
    )


class XYEmittanceTable(Table):
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
