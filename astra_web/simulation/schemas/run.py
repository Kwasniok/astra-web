from pydantic import Field, computed_field
from astra_web.file import IniExportableModel


class SimulationRunSpecifications(IniExportableModel):

    # web exclusive fields:
    comment: str | None = Field(
        default=None,
    )
    generator_id: str = Field(
        default="YYYY-MM-DD-HH-MM-SS-UUUUUUUU",
        description="Identifier of a particle distribution generated with the /generate endpoint of this API.",
    )
    thread_num: int = Field(
        default=1,
        gt=0,
        description="The number of concurrent threads used per simulation.",
    )
    timeout: int = Field(
        default=600,
        description="The timeout for the simulation run. Simulation terminated if timeout time is exceeded.",
        json_schema_extra={"format": "Unit: [s]"},
    )

    def excluded_ini_fields(self) -> set[str]:
        return super().excluded_ini_fields() | {
            "comment",
            "thread_num",
            "timeout",
            "generator_id",
        }

    # ASTRA fields:
    @computed_field(
        alias="Head",
        repr=True,
        description="Run name for protocol",
    )
    @property
    def head(self) -> str:
        return f"Created with astra_web. Initial particle distribution ID: `{self.generator_id}`."

    @computed_field(
        alias="RUN",
        description="The `run_number` is used as extension for all generated output files.",
    )
    @property
    def run_number(self) -> int:
        return 1

    # looping: skipped

    @computed_field(
        alias="Distribution",
        description="Name of the file containing the initial particle distribution to be used.",
        repr=True,
    )
    @property
    def distribution_file_name(self) -> str:
        # name initial particle distribution file in the same convention as the run output files
        # see manual of ASTRA v3.2 (Mach 2017) chapter 2
        return f"run.{0:04d}.{self.run_number:03d}"

    # ions: skipped

    bunch_reduction_num: float | None = Field(
        default=1,
        alias="N_red",
        validation_alias="bunch_reduction_num",
        description="Use every `bunch_reduction_num`-th particle in the simulation only.",
    )
    bunch_initial_shift_x: float | None = Field(
        default=0.0,
        alias="Xoff",
        validation_alias="bunch_initial_shift_x",
        description="Horizontal offset of the input particle distribution.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    bunch_initial_shift_y: float | None = Field(
        default=0.0,
        alias="Yoff",
        validation_alias="bunch_initial_shift_y",
        description="Vertical offset of the input particle distribution.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    bunch_initial_rotation_x: float | None = Field(
        default=0.0,
        alias="xp",
        validation_alias="bunch_initial_rotation_x",
        description="Horizontal rotation of the input particle distribution.",
        json_schema_extra={"format": "Unit: [rad]"},
    )
    bunch_initial_rotation_y: float | None = Field(
        default=0.0,
        alias="yp",
        validation_alias="bunch_initial_rotation_y",
        description="Vertical rotation of the input particle distribution.",
        json_schema_extra={"format": "Unit: [rad]"},
    )
    bunch_initial_shift_z: float | None = Field(
        default=0.0,
        alias="Zoff",
        validation_alias="bunch_initial_shift_z",
        description="Longitudinal offset of the input particle distribution.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    bunch_initial_shift_t: float | None = Field(
        default=0.0,
        alias="Toff",
        validation_alias="bunch_initial_shift_t",
        description="Temporal offset of the input particle distribution.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    bunch_initial_x_rms: float | None = Field(
        default=None,
        alias="Xrms",
        validation_alias="bunch_initial_x_rms",
        description="Horizontal RMS beam size of the input particle distribution. Scaling is active for positive values.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    bunch_initial_y_rms: float | None = Field(
        default=None,
        alias="Yrms",
        validation_alias="bunch_initial_y_rms",
        description="Vertical RMS beam size of the input particle distribution. Scaling is active for positive values.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    bunch_initial_xy_rms: float | None = Field(
        default=None,
        alias="XYrms",
        validation_alias="bunch_initial_xy_rms",
        description="Horizontal and vertical RMS beam size of the input particle distribution. Scaling is active for positive values. This takes *priority* over `bunch_initial_x_rms` and `bunch_initial_y_rms`.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    bunch_initial_z_rms: float | None = Field(
        default=None,
        alias="Zrms",
        validation_alias="bunch_initial_z_rms",
        description="Longitudinal RMS beam size/bunch length of the input particle distribution. Scaling is active for positive values.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    bunch_initial_t_rms: float | None = Field(
        default=None,
        alias="Trms",
        validation_alias="bunch_initial_t_rms",
        description="Temporal RMS beam size/emission time of the input particle distribution. Scaling is active for positive values.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    emission_delay_time_tau: float | None = Field(
        default=None,
        alias="Tau",
        validation_alias="emission_delay_time_tau",
        description="Coefficient of the exponential delay time of the emission. Active if non-zero. Note that the delay time is random and might interfere with the quasi random nature of an input distribution.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    bunch_initial_correlated_divergence_px: float | None = Field(
        default=None,
        alias="cor_px",
        validation_alias="bunch_initial_correlated_divergence_px",
        description="Horizontal correlated divergence of the bunch. Active if non-zero.",
        json_schema_extra={"format": "Unit: [mrad]"},
    )
    bunch_initial_correlated_divergence_py: float | None = Field(
        default=None,
        alias="cor_py",
        validation_alias="bunch_initial_correlated_divergence_py",
        description="Vertical correlated divergence of the bunch. Active if non-zero.",
        json_schema_extra={"format": "Unit: [mrad]"},
    )
    bunch_initial_charge: float | None = Field(
        default=None,
        alias="Qbunch",
        validation_alias="bunch_initial_charge",
        description="Bunch charge in [nC]. Scaling is active if bunch_initial_charge != 0.",
        json_schema_extra={"format": "Unit: [nC]"},
    )
    bunch_initial_schottky_coefficient_sqrt: float | None = Field(
        default=None,
        alias="SQR_Q_Schottky",
        validation_alias="bunch_initial_schottky_coefficient_sqrt",
        description="Square root variation of the bunch charge with the field on the cathode. Scaling is active if non-zero.",
        json_schema_extra={"format": "Unit: [nC {m/MV}^{1/2}]"},
    )
    bunch_initial_schottky_coefficient_linear: float | None = Field(
        default=None,
        alias="Q_Schottky",
        validation_alias="bunch_initial_schottky_coefficient_linear",
        description="Linear variation of the bunch charge with the field on the cathode. Scaling is active if non-zero.",
        json_schema_extra={"format": "Unit: [nC m/MV]"},
    )
    particle_debunch: float | None = Field(
        default=None,
        alias="debunch",
        validation_alias="particle_debunch",
        description="'debunched' particles, i.e. particles with a distance to the bunch center exceeding debunch· σ_z are passivated, i.e. their status will be set to 0 or 1. Debunch is defined relative to the rms bunch length, hence it should not be used close to the cathode where σ_z can be zero. The procedure is active when non-zero.",
    )
    particle_track_all: bool | None = Field(
        default=True,
        alias="Track_All",
        validation_alias="particle_track_all",
        description="If false, only the reference particle will be tracked.",
    )
    particle_track_reference_on_axis: bool | None = Field(
        default=False,
        alias="Track_On_Axis",
        validation_alias="particle_track_reference_on_axis",
        description="If true, the reference particle will be tracked only on axis. The ref file contains the on-axis results in this case..",
    )
    cavity_phase_auto: bool | None = Field(
        default=True,
        alias="Auto_Phase",
        validation_alias="cavity_phase_auto",
        description="If true, the RF phases will be set relative to the phase with maximum energy gain.",
    )
    cavity_phase_scan: bool | None = Field(
        default=False,
        alias="Phase_Scan",
        validation_alias="cavity_phase_scan",
        description="If true, the RF phases of the cavities will be scanned between 0 and 360 degree. Results are saved in the PScan file. The tracking between cavities will be done with the user-defined phases.",
    )
    tracking_interrupt_on_reference_particle_loss: bool | None = Field(
        default=True,
        alias="check_ref_part",
        validation_alias="tracking_interrupt_on_reference_particle_loss",
        description="If true, the run will be interrupted if the reference particle is lost during the on and off-axis reference particle tracking.",
    )
    particle_remove_when_traveling_backwards: bool | None = Field(
        default=False,
        alias="L_rm_back",
        validation_alias="particle_remove_when_traveling_backwards",
        description="If true, particles are immediately discarded when they start to travel backwards. If false, backward traveling particles are only discarded when they pass the lower boundary `z_min`. Note, that in some cases (phases) the particles can change the direction of motion several times, before hitting a boundary.",
    )
    z_min: float | None = Field(
        default=None,
        alias="Z_min",
        validation_alias="z_min",
        description="Lower boundary for discarding particles. If not specified it is automatically set by the program assuming that particles are supposed to travel in positive Z-direction.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    z_cathode: float | None = Field(
        default=None,
        alias="Z_Cathode",
        validation_alias="z_cathode",
        description="Position of the cathode for the calculation of the mirror charge. If not specified it is automatically set by the program to the minimal particle position provided the bunch is emitted from a cathode.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    integrator_step_min: float | None = Field(
        default=None,
        alias="H_min",
        validation_alias="integrator_step_min",
        description="Minimum time step for the Runge-Kutta integration and min. time step during emission (with full space charge calculations). When zero, the step size will be automatically set to `integrator_step_min = bunch_initial_time * bunch_initial_particle_num_avg / bunch_initial_particles_total` (see ASTRA Manual v3 Eq. (4.1)).",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    integrator_step_max: float | None = Field(
        default=0.001,
        alias="H_max",
        validation_alias="integrator_step_max",
        description="Maximum time step for the Runge-Kutta integration.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    integrator_iteration_max: int | None = Field(
        default=100_000,
        alias="Max_step",
        validation_alias="integrator_iteration_max",
        description="Safety measure. After this many Runge-Kutta steps the run is terminated.",
    )

    def to_ini(self, indent: int = 4) -> str:
        return f"&NEWRUN{super().to_ini(indent=indent)}/"
