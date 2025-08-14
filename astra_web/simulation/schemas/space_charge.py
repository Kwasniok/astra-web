from pydantic import Field, computed_field
from astra_web.file import IniExportableModel


class SpaceCharge(IniExportableModel):

    # ASTRA fields:

    # loop: skipped

    enable: bool | None = Field(
        default=False,
        alias="LSPCH",
        validation_alias="enable",
        description="Toggle whether to calculate space charge fields or not.",
    )
    start_with_grid_3d: bool | None = Field(
        default=False,
        alias="LSPCH3D",
        validation_alias="start_with_grid_3d",
        description="Toggle whether to initially start with a cartesian 3D grid. Note: Not all features are available for 3D!",
    )

    @computed_field(repr=True)
    @property
    def L2D_3D(self) -> bool | None:
        return self.grid_transition_z is not None

    enable_mirror_charge: bool | None = Field(
        default=True,
        alias="Lmirror",
        validation_alias="enable_mirror_charge",
        description="Cylindrical coords (2D) only: If true, mirror charges at the cathode are taken into account.",
    )

    # L_Curved_Cathode, Cathode_Contour, R_zero (non-planar cathode): skipped

    grid_2d_radial_cell_count: int | None = Field(
        gt=0,
        default=10,
        alias="Nrad",
        validation_alias="grid_2d_radial_cell_count",
        description="Cylindrical coords (2D) only: Number of grid cells in radial direction up to the bunch radius.",
    )
    grid_2d_radial_innermost_cell_scale_factor: float | None = Field(
        default=2.0,
        alias="Cell_var",
        validation_alias="grid_2d_radial_innermost_cell_scale_factor",
        description="Cylindrical coords (2D) only: Variation of the cell height in radial direction. The innermost cell is this many times higher than the outermost cell",
    )
    grid_2d_longitudinal_cell_count: int | None = Field(
        default=10,
        alias="Nlong_in",
        validation_alias="grid_2d_longitudinal_cell_count",
        description="Cylindrical coords (2D) only: Maximum number of grid cells in longitudinal direction within the bunch length. During the emission process the number is reduced, according to the specification of the minimum cell length min_grid.",
    )
    emitted_particle_num_per_step: int | None = Field(
        default=30,
        alias="N_min",
        validation_alias="emitted_particle_num_per_step",
        description="Cylindrical coords (2D) only: Average number of particles to be emitted in one step during the emission from  a cathode. This is needed to set `integrator_step_min` (`step_size`) automatically during emission.",
    )

    # Merge_* : skipped

    grid_transition_z: float | None = Field(
        default=None,
        alias="z_trans",
        validation_alias="grid_transition_z",
        description="Cylindrical coords (2D) to cartesian coords (3D) only: Longitudinal position for automatic transition of 2D to 3D space charge calculation.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    grid_transition_longitudinal_cell_count_min: int | None = Field(
        default=None,
        alias="min_grid_trans",
        validation_alias="grid_transition_longitudinal_cell_count_min",
        description="Cylindrical coords (2D) to cartesian coords (3D) only: Minimal longitudinal length of 2D grid cells during automatic transition of 2D to 3D space charge calculation.",
    )
    grid_3d_x_cell_count: int | None = Field(
        default=8,
        ge=4,
        alias="Nxf",
        validation_alias="grid_3d_x_cell_count",
        description="Cartesian coords (3D) only: Maximum number of grid cells in x direction within the bunch length.",
    )
    grid_3d_x_empty_cell_count: int | None = Field(
        default=2,
        alias="Nx0",
        validation_alias="grid_3d_x_empty_cell_count",
        description="Cartesian coords (3D) only: Number of empty boundary grid cells in x direction within the bunch length.",
    )
    grid_3d_y_cell_count: int | None = Field(
        default=8,
        ge=4,
        alias="Nyf",
        validation_alias="grid_3d_y_cell_count",
        description="Cartesian coords (3D) only: Maximum number of grid cells in y direction within the bunch length.",
    )
    grid_3d_y_empty_cell_count: int | None = Field(
        default=2,
        alias="Ny0",
        validation_alias="grid_3d_y_empty_cell_count",
        description="Cartesian coords (3D) only: Number of empty boundary grid cells in y direction within the bunch length.",
    )
    grid_3d_z_cell_count: int | None = Field(
        default=8,
        ge=4,
        alias="Nzf",
        validation_alias="grid_3d_z_cell_count",
        description="Cartesian coords (3D) only: Maximum number of grid cells in z direction within the bunch length.",
    )
    grid_3d_z_empty_cell_count: int | None = Field(
        default=2,
        alias="Nz0",
        validation_alias="grid_3d_z_empty_cell_count",
        description="Cartesian coords (3D) only: Number of empty boundary grid cells in z direction within the bunch length.",
    )
    grid_3d_smoothing_x: int | None = Field(
        default=0,
        alias="Smooth_x",
        validation_alias="grid_3d_smoothing_x",
        description="Cartesian coords (3D) only: Smoothing factor for the x direction.",
    )
    grid_3d_smoothing_y: int | None = Field(
        default=0,
        alias="Smooth_y",
        validation_alias="grid_3d_smoothing_y",
        description="Cartesian coords (3D) only: Smoothing factor for the y direction.",
    )
    grid_3d_smoothing_z: int | None = Field(
        default=0,
        alias="Smooth_z",
        validation_alias="grid_3d_smoothing_z",
        description="Cartesian coords (3D) only: Smoothing factor for the z direction.",
    )
    scaling_relative_deviation_threshold: float | None = Field(
        default=0.05,
        alias="Max_Scale",
        validation_alias="scaling_relative_deviation_threshold",
        description="If one of the space charge scaling factors exceeds the limit 1± `scaling_relative_deviation_threshold` a new space charge calculation is initiated.",
    )
    scaling_step_threshold: int | None = Field(
        default=40,
        gt=0,
        alias="Max_Count",
        validation_alias="scaling_step_threshold",
        description="If the space charge field has been scaled `scaling_step_threshold` times, a new space charge calculation is initiated. A value of 1 disables the scaling entirely.",
    )
    variation_threshold: float | None = Field(
        default=0.1,
        alias="Exp_Control",
        validation_alias="variation_threshold",
        description="Specifies the maximum tolerable variation of the bunch extensions relative to \
                    the grid cell size within one time step.",
    )

    def to_ini(self, indent: int = 4) -> str:
        return f"&CHARGE{super().to_ini(indent=indent)}/"
