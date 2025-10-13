from pydantic import Field
from astra_web.file import IniExportableModel, IniExportableArrayModel


class SimulationOutputScreen(IniExportableModel):

    # ASTRA fields:
    z: float = Field(
        description="Position of the screen.",
        alias="Screen",
        validation_alias="z",
        json_schema_extra={"format": "Unit: [m]"},
    )
    angle_x: float | None = Field(
        default=None,
        description="Rotation angle of the screen in the x-z plane. Active if non-zero and only in combination with `emittance_local`. The angles are measured relative to the z-axis, i. e. the standard position corresponds to π/2.",
        alias="Scr_xrot",
        validation_alias="angle_x",
        json_schema_extra={"format": "Unit: [rad]"},
    )
    angle_y: float | None = Field(
        default=None,
        description="Rotation angle of the screen in the y-z plane. Active if non-zero and only in combination with `emittance_local`. The angles are measured relative to the z-axis, i. e. the standard position corresponds to π/2.",
        alias="Scr_yrot",
        validation_alias="angle_y",
        json_schema_extra={"format": "Unit: [rad]"},
    )


class SimulationOutputSpecification(IniExportableModel):

    def excluded_ini_fields(self) -> set[str]:
        return super().excluded_ini_fields() | {"screens"}

    # ASTA fields:
    z_start: float = Field(
        default=0.0,
        alias="ZSTART",
        validation_alias="z_start",
        description="Minimal longitudinal position for the generation of output. Tracking may start at `z != z_start`.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    z_stop: float = Field(
        default=1.0,
        alias="ZSTOP",
        validation_alias="z_stop",
        description="Maximal longitudinal position for the bunch center.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    emittance_intervals: int = Field(
        default=100,
        alias="Zemit",
        validation_alias="emittance_intervals",
        description="The interval `z_stop - z_start` is divided into `emittance_intervals` sub-intervals. At the end of  each sub-interval statistical bunch parameters such as emittance are saved. It is advised to set a multiple of `distribution_intervals` as value.",
        gt=1,
    )
    distribution_intervals: int = Field(
        default=1,
        alias="Zphase",
        validation_alias="distribution_intervals",
        description="The interval `z_stop - z_start` is divided into `distribution_intervals` sub-intervals. At the end of each sub-interval (rounded to nearest emittance interval) a complete particle distribution is saved. It is advised to set a whole fraction of `distribution_intervals` as value.",
    )
    # note: ASTRA has an arbitrary limit of 8 items here.
    screens: IniExportableArrayModel[SimulationOutputScreen] = Field(
        default_factory=IniExportableArrayModel[SimulationOutputScreen],
        description="The quantity to be optimized.",
    )
    step_width: float | None = Field(
        default=0,
        alias="Step_width",
        validation_alias="step_width",
        description="Output generation based on time steps rather than on positions. Output is generated every `step_width` * time_step.",
    )
    step_max: float | None = Field(
        default=0,
        alias="Step_max",
        validation_alias="step_max",
        description="Terminates output based on Step_width. Run may continue if `integrator_iteration_max > step_max`.",
    )
    emittance_projected: bool | None = Field(
        default=False,
        alias="Lproject_emit",
        validation_alias="project_emittance",
        description="If true, the transverse particle positions of all particles will be projected into a common plane at the longitudinal bunch center position prior to the calculation of the emittance, spot size etc.",
    )
    emittance_local: bool | None = Field(
        default=False,
        alias="Local_emit",
        validation_alias="emittance_local",
        description="If true, the transverse particle positions of all particles will be recorded when passing the output position plane prior to the calculation of the emittance, spot size etc. The longitudinal particle coordinates in output files are recalculated based on times and velocities and are only approximate. Hence distributions saved with this option should not be used as input distributions for further tracking! The distance between subsequent output positions has to be larger than the bunch length, or they will be skipped.",
    )
    emittance_ignore_solenoids: bool | None = Field(
        default=False,
        alias="Lmagnetized",
        validation_alias="emittance_ignore_solenoids",
        description="If true, solenoid fields are neglected in the calculation of the beam emittance.",
    )
    emittance_subtract_angular_momentum: bool | None = Field(
        default=False,
        alias="Lsub_rot",
        validation_alias="emittance_subtract_angular_momentum",
        description="If true `emittance_ignore_solenoids` will be treated as true and the angular momentum of the bunch is subtracted for the emittance calculation based on the actual x-py and y-px correlation of the bunch rather than by the canonical momentum.",
    )
    emittance_subtract_larmor: bool | None = Field(
        default=False,
        alias="Lsub_Larmor",
        validation_alias="emittance_subtract_larmor",
        description="If true a rotation of the transverse coordinate system induced by a solenoid will be taken into account.",
    )
    emittance_correct_transverse_beam_tilt: bool | None = Field(
        default=False,
        alias="Lsub_coup",
        validation_alias="emittance_correct_transverse_beam_tilt",
        description="If true a rotation angle of the transverse beam spot will be corrected before the emittance is calculated.",
    )
    emittance_rotation_angle: float | None = Field(
        default=None,
        alias="Rot_ang",
        validation_alias="emittance_rotation_angle",
        description="Rotation angle for emittance calculation in connection with `emittance_correct_transverse_beam_tilt`. If no rotation angle is specified an optimized rotation angle will be taken.",
    )
    emittance_include_reduced: bool | None = Field(
        default=False,
        alias="Lsub_cor",
        validation_alias="emittance_include_reduced",
        description="If true the reduced emittance is calculated in addition to the standard emittance",
    )
    save_off_axis_reference_trajectory: bool | None = Field(
        default=False,
        alias="RefS",
        validation_alias="save_off_axis_reference_trajectory",
        description="If true, ASTRA store output of the off-axis reference trajectory, energy gain etc. at each Runge-Kutta time step.",
    )
    save_emittance: bool | None = Field(
        default=False,
        alias="EmitS",
        validation_alias="save_emittance",
        description="If true, output of the beam emittance and other statistical beam parameters is generated. The parameters are calculated and stored at the end of each sub-interval defined by `emittance_intervals`.",
    )
    save_emittance_core_80_99: bool | None = Field(
        default=False,
        alias="C_EmitS",
        validation_alias="save_emittance_core_80_99",
        description="If true, output core emittance for 80%, 90%, 95%.",
    )
    save_emittance_core_99: bool | None = Field(
        default=False,
        alias="C99_EmitS",
        validation_alias="save_emittance_core_99",
        description="If true, output core emittance for 99%, 99.9%, 99.99%.",
    )
    save_emittance_trace_space: bool | None = Field(
        default=False,
        alias="TR_emitS",
        validation_alias="save_emittance_trace_space",
        description="If true, output of the trace space beam emittance and other statistical beam parameters is generated.",
    )
    save_emittance_sub_ensemble: bool | None = Field(
        default=False,
        alias="Sub_EmitS",
        validation_alias="save_emittance_sub_ensemble",
        description="If true, output of the sub ensemble space beam emittance and other statistical beam parameters is generated.",
    )

    # cross skipped

    save_distribution: bool | None = Field(
        default=False,
        alias="PhaseS",
        validation_alias="save_distribution",
        description="If true, the complete particle distribution is saved at distribution_intervals different locations as well as at screens and wake positions.",
    )
    save_distribution_by_time: bool | None = Field(
        default=False,
        alias="T_PhaseS",
        validation_alias="save_distribution_by_time",
        description="If true, the complete particle distribution is saved at each `step_width * time_step`.",
    )
    save_distribution_with_high_resolution: bool | None = Field(
        default=False,
        alias="High_res",
        validation_alias="save_distribution_with_high_resolution",
        description="If true, particle distributions are saved with increased accuracy.",
    )
    save_distribution_as_binary: bool | None = Field(
        default=False,
        alias="Binary",
        validation_alias="save_distribution_as_binary",
        description="If true, particle distributions are saved as binary files.",
    )
    save_probe_particles: bool | None = Field(
        default=False,
        alias="TrackS",
        validation_alias="save_probe_particles",
        description="If true, the probe particle trajectories with space charge fields acting on them are saved per Runge-Kutta time step.",
    )
    save_space_charge_scaling: bool | None = Field(
        default=False,
        alias="TcheckS",
        validation_alias="save_space_charge_scaling",
        description="If true, the development of the space charge scaling is stored.",
    )
    save_sigmas: bool | None = Field(
        default=False,
        alias="SigmaS",
        validation_alias="save_sigmas",
        description="If true, the development of the sigmas is stored.",
    )
    save_space_charge_field_on_cathode: bool | None = Field(
        default=False,
        alias="CathodeS",
        validation_alias="save_space_charge_field_on_cathode",
        description="If true, the space charge field on the cathode is stored per Runge-Kutta time step.",
    )
    save_particle_statistics: bool | None = Field(
        default=False,
        alias="LandFS",
        validation_alias="save_particle_statistics",
        description="If true, the development of the particle statistics is stored per `distribution_interval` and screen..",
    )
    save_larmor_angle_statistics: bool | None = Field(
        default=False,
        alias="LarmorS",
        validation_alias="save_larmor_angle_statistics",
        description="If true, the development of the Larmor angle statistics is stored per `emittance_interval`.",
    )

    def to_ini(self, indent: int = 4) -> str:
        s = "&OUTPUT"
        s += super().to_ini(indent=indent)
        if self.screens.values:
            s += self.screens.to_ini(indent=indent)
        s += "/"
        return s
