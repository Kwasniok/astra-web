import os
from abc import ABC, abstractmethod
from typing import Any
from pydantic import Field, ConfigDict, computed_field
from .tables import FieldTable
from astra_web.file import IniExportableModel


class Module(IniExportableModel, ABC):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(exclude=True, default=-1, description="The ID of the module.")

    def _to_ini_dict(self) -> dict[str, Any]:
        # non-excluded, non-none, aliased fields with enumeration suffixes

        out_dict = super()._to_ini_dict()
        out_dict = {f"{k}({self.id})": v for k, v in out_dict.items()}
        return out_dict

    @abstractmethod
    def write_to_csv(self, run_path: str) -> None:
        """
        Write the module's data to disk as CSV file.
        """
        pass


class Cavity(Module):
    model_config = ConfigDict(extra="forbid")

    field_table: FieldTable | None = Field(
        exclude=True,
        default=None,
        description="Table containing lists of longitudinal positions z and corresponding \
                    field amplitudes v in free units.",
        json_schema_extra={"format": "Unit: [m]"},
    )

    @computed_field
    @property
    def File_Efield(self) -> str:
        return f"C{self.id}_E.dat"

    frequency: float = Field(
        default=1.3e0,
        alias="Nue",
        validation_alias="frequency",
        description="Frequency of the RF field.",
        json_schema_extra={"format": "Unit: [GHz]"},
    )
    z_0: float = Field(
        default=0.0e0,
        alias="C_pos",
        validation_alias="z_0",
        description="Leftmost longitudinal cavity position.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    smoothing_iterations: int = Field(
        default=10,
        alias="C_smooth",
        validation_alias="smoothing_iterations",
        description="Number of iterations for smoothing of transverse field components.",
    )
    higher_order: bool = Field(
        default=True,
        alias="C_higher_order",
        validation_alias="higher_order",
        description="If true, field expansion extends to 3rd order, 1st order if false.",
    )
    phase: float = Field(
        default=0.0e0,
        alias="Phi",
        validation_alias="phase",
        description="Initial phase of the RF field.",
        json_schema_extra={"format": "Unit: [deg]"},
    )
    max_field_strength: float = Field(
        default=130.0e0,
        alias="MaxE",
        validation_alias="max_field_strength",
        description="Maximum on-axis longitudinal amplitude of the RF field",
        json_schema_extra={"format": "Unit: [MV/m] | [T]"},
    )

    def write_to_csv(self, run_path: str) -> None:
        """Write the field table to a CSV file in the specified path."""
        if self.field_table is None:
            return
        self.field_table.write_to_csv(os.path.join(run_path, self.File_Efield))

    def _to_ini_dict(self) -> dict[str, Any]:
        out_dict = super()._to_ini_dict()
        out_dict[f"File_Efield({self.id})"] = self.File_Efield

        return out_dict


class Solenoid(Module):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    field_table: FieldTable | None = Field(
        default=None,
        exclude=True,
        description="Table containing lists of longitudinal positions z and corresponding \
                    field amplitudes v in free units.",
        json_schema_extra={"format": "Unit: [m]"},
    )

    @computed_field
    @property
    def File_Bfield(self) -> str:
        return f"S{self.id}_B.dat"

    z_0: float | None = Field(
        default=None,
        alias="S_pos",
        validation_alias="z_0",
        description="Leftmost longitudinal solenoid position.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    smoothing_iterations: int = Field(
        default=10,
        alias="S_smooth",
        validation_alias="smoothing_iterations",
        description="Number of iterations for smoothing of transverse field components.",
    )
    max_field_strength: float | None = Field(
        default=None,
        alias="MaxB",
        validation_alias="max_field_strength",
        description="Maximum on-axis longitudinal amplitude of the magnetic field.",
        json_schema_extra={"format": "Unit: [T]"},
    )

    def _to_ini_dict(self) -> dict[str, Any]:
        out_dict = super()._to_ini_dict()
        out_dict[f"File_Bfield({self.id})"] = self.File_Bfield

        return out_dict

    def write_to_csv(self, run_path: str) -> None:
        """Write the field table to a CSV file in the specified path."""
        if self.field_table is None:
            return
        self.field_table.write_to_csv(os.path.join(run_path, self.File_Bfield))
