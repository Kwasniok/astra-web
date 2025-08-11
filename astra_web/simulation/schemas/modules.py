from typing import Any
from pydantic import Field
from astra_web.file import IniExportableModel


class Module(IniExportableModel):

    def excluded_ini_fields(self) -> set[str]:
        return super().excluded_ini_fields() | {
            "id",
            "comment",
        }

    id: int = Field(default=-1, description="The ID of the module.")
    comment: str | None = Field(
        default=None, description="Optional comment for the module."
    )

    def _to_ini_dict(self) -> dict[str, Any]:
        # non-excluded, non-none, aliased fields with enumeration suffixes

        out_dict = super()._to_ini_dict()
        out_dict = {f"{k}({self.id})": v for k, v in out_dict.items()}
        return out_dict


class Cavity(Module):

    field_file_name: str = Field(
        description="Name of the field file for the longitudinal on-axis electric field amplitudes.",
        alias="File_Efield",
        validation_alias="field_file_name",
    )

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


class Solenoid(Module):

    field_file_name: str = Field(
        description="Name of the field file for the longitudinal on-axis magnetic field amplitudes.",
        alias="File_Bfield",
        validation_alias="field_file_name",
    )

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
