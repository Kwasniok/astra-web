from enum import Enum
from pydantic import Field
from astra_web.file import IniExportableModel


class Module(IniExportableModel):

    comment: str | None = Field(
        default=None, description="Optional comment for the module."
    )

    def excluded_ini_fields(self) -> set[str]:
        return super().excluded_ini_fields() | {
            "comment",
        }


class CavityFieldComponents(str, Enum):
    ALL = "all"
    EB = "E,B"


class Cavity(Module):

    # ASTRA fields:

    # loop: skipped

    # LEField: not sensible for single cavity

    field_file_name: str = Field(
        description="Name of the field file for the longitudinal on-axis electric field amplitudes.",
        alias="File_Efield",
        validation_alias="field_file_name",
    )
    disable_scale: bool | None = Field(
        default=False,
        alias="C_noscale",
        validation_alias="disable_scale",
        description="If true, the scaling of the RF field is disabled. File values will be taken as field values in MV/m  or T.",
    )
    smoothing_iterations: int | None = Field(
        default=0,
        alias="C_smooth",
        validation_alias="smoothing_iterations",
        description="Number of iterations for smoothing of transverse field components.",
    )
    field_components: CavityFieldComponents | None = Field(
        default=None,
        alias="Com_grid",
        validation_alias="field_components",
        description="Grid choice for the field components.",
    )
    higher_order: bool = Field(
        default=True,
        alias="C_higher_order",
        validation_alias="higher_order",
        description="If true, field expansion extends to 3rd order, 1st order if false.",
    )
    frequency: float = Field(
        alias="Nue",
        validation_alias="frequency",
        description="Frequency of the RF field.",
        json_schema_extra={"format": "Unit: [GHz]"},
    )
    wave_number: float | None = Field(
        default=None,
        alias="K_wave",
        validation_alias="wave_number",
        description="Wave number of the field, only for β matched traveling wave structures.",
        json_schema_extra={"format": "Unit: [1/m]"},
    )
    max_field_strength: float = Field(
        default=130.0e0,
        alias="MaxE",
        validation_alias="max_field_strength",
        description="Maximum on-axis longitudinal amplitude of the RF field",
        json_schema_extra={"format": "Unit: [MV/m] | [T]"},
    )

    # Ex_stat, ...: skipped

    flatness: float | None = Field(
        default=0.0,
        alias="Flatness",
        validation_alias="flatness",
        description="Modifies the field flatness by multiplying the longitudinal field component with a linear slope; applied after scaling to `max_field_strength`. Not applicable for 3D and TWS structures.",
    )
    phase: float = Field(
        alias="Phi",
        validation_alias="phase",
        description="Initial phase of the RF field.",
        json_schema_extra={"format": "Unit: [deg]"},
    )
    z: float = Field(
        alias="C_pos",
        validation_alias="z",
        description="Shifts the longitudinal cavity position (relative to values in file).",
        json_schema_extra={"format": "Unit: [m]"},
    )
    number_of_cells_or_periods: float | None = Field(
        default=None,
        alias="C_numb",
        validation_alias="number_of_cells_or_periods",
        description="Number of cells excluding the input and output cell for traveling wave structures, or number of periods for 3D maps.",
    )
    time_dependence_type: str | None = Field(
        default=None,
        alias="T_dependence",
        validation_alias="time_dependence_type",
        description="Either `fill` or `decay` in order to activate filling or decaying of the cavity field, respectively.",
    )
    time_dependence_null: float | None = Field(
        default=None,
        alias="T_null",
        validation_alias="time_dependence_null",
        description="For cavity filling: time between start of the filling of the cavity and start of the particle tracking; for decay: time between start of decay and start of particle tracking.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    time_dependence_tau: float | None = Field(
        default=None,
        alias="T_tau",
        validation_alias="time_dependence_tau",
        description="Filling time of the cavity.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    stored_energy: float | None = Field(
        default=None,
        alias="T_stored",
        validation_alias="stored_energy",
        description="Stored energy in the cavity. If specified beam loading is taken into account.",
        json_schema_extra={"format": "Unit: [J m^2/MV^2]"},
    )
    shift_x: float | None = Field(
        default=0.0,
        alias="C_xoff",
        validation_alias="shift_x",
        description="Horizontal shift of the cavity.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    shift_y: float | None = Field(
        default=0.0,
        alias="C_yoff",
        validation_alias="shift_y",
        description="Vertical shift of the cavity.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    angle_x: float | None = Field(
        default=0.0,
        alias="C_xrot",
        validation_alias="angle_x",
        description="Rotation angle of the cavity in the x-z plane, i.e. around the y-axis.",
        json_schema_extra={"format": "Unit: [rad]"},
    )
    angle_y: float | None = Field(
        default=0.0,
        alias="C_yrot",
        validation_alias="angle_y",
        description="Rotation angle of the cavity in the y-z plane, i.e. around the x-axis.",
        json_schema_extra={"format": "Unit: [rad]"},
    )
    angle_z: float | None = Field(
        default=0.0,
        alias="C_zrot",
        validation_alias="angle_z",
        description="Rotation angle of the cavity in the x-y plane, i.e. around the z-axis.",
        json_schema_extra={"format": "Unit: [rad]"},
    )
    local_field_offset_start: float | None = Field(
        default=None,
        alias="C_zkickmin",
        validation_alias="local_field_offset_start",
        description="Start of local field offset.",
        json_schema_extra={"format": "Unit: [m]"},
    )

    local_field_offset_stop: float | None = Field(
        default=None,
        alias="C_zkickmax",
        validation_alias="local_field_offset_stop",
        description="Stop of local field offset.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    local_field_shift_x: float | None = Field(
        default=0.0,
        alias="C_Xkick",
        validation_alias="local_field_shift_x",
        description="Shift of the local field in the x-direction.",
        json_schema_extra={"format": "Unit: [m]"},
    )

    local_field_shift_y: float | None = Field(
        default=0.0,
        alias="C_Ykick",
        validation_alias="local_field_shift_y",
        description="Shift of the local field in the y-direction.",
        json_schema_extra={"format": "Unit: [m]"},
    )

    # File_A0, P_* (plasma): skipped

    # E_*,zeta (laser): skipped


class Solenoid(Module):

    # ASTRA fields:

    # loop: skipped

    # LBfield: not sensible for single solenoid

    field_file_name: str = Field(
        description="Name of the field file for the longitudinal on-axis magnetic field amplitudes.",
        alias="File_Bfield",
        validation_alias="field_file_name",
    )
    disable_scaling: bool | None = Field(
        default=False,
        alias="S_noscale",
        validation_alias="disable_scaling",
        description="Disable scaling of the magnetic field. File values will be taken as field values in T.",
    )
    smoothing_iterations: int | None = Field(
        default=0,
        alias="S_smooth",
        validation_alias="smoothing_iterations",
        description="Controls the number of iterations of a soft, iterative procedure for smoothing field tables. Since the transverse field components are based on derivatives of the field table and can be noisy if the table is not precise, smoothing is recommended. Use fieldplot to check that the longitudinal field component remains basically unchanged and that the transverse components get smooth.",
    )
    higher_order: bool | None = Field(
        default=False,
        alias="S_higher_order",
        validation_alias="higher_order",
        description="If true, the field expansion extends to 3rd order, if false the field expansion extends only to 1st order. If true stronger smoothing of the field might be required.",
    )
    max_field_strength: float | None = Field(
        default=None,
        alias="MaxB",
        validation_alias="max_field_strength",
        description="Maximum on-axis longitudinal amplitude of the magnetic field.",
        json_schema_extra={"format": "Unit: [T]"},
    )
    z: float | None = Field(
        default=None,
        alias="S_pos",
        validation_alias="z",
        description="Shifts the longitudinal solenoid position (relative to values in file).",
        json_schema_extra={"format": "Unit: [m]"},
    )
    shift_x: float | None = Field(
        default=0.0,
        alias="S_xoff",
        validation_alias="shift_x",
        description="Horizontally shift the solenoid field.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    shift_y: float | None = Field(
        default=0.0,
        alias="S_yoff",
        validation_alias="shift_y",
        description="Vertically shift the solenoid field.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    angle_x: float | None = Field(
        default=0.0,
        alias="S_xrot",
        validation_alias="angle_x",
        description="Rotation angle of the solenoid in the x-z plane, i.e. around the y-axis.",
        json_schema_extra={"format": "Unit: [rad]"},
    )
    angle_y: float | None = Field(
        default=0.0,
        alias="S_yrot",
        validation_alias="angle_y",
        description="Rotation angle of the solenoid in the y-z plane, i.e. around the x-axis.",
        json_schema_extra={"format": "Unit: [rad]"},
    )
