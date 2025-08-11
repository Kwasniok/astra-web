from pydantic import Field, computed_field
from astra_web.file import IniExportableModel


class SimulationRunSpecifications(IniExportableModel):

    Version: int = Field(default=4)

    def excluded_ini_fields(self) -> set[str]:
        return super().excluded_ini_fields() | {
            "thread_num",
            "timeout",
            "generator_id",
        }

    @computed_field(description="Run name for protocol", repr=True)
    @property
    def Head(self) -> str:
        return f"Simulation run with initial particle distribution {self.generator_id}"

    thread_num: int = Field(
        default=1,
        gt=0,
        description="The number of concurrent threads used per simulation.",
    )

    z_min: float | None = Field(
        default=None,
        alias="Z_min",
        validation_alias="z_min",
        description="Lower boundary for discarding particles.",
    )

    timeout: int = Field(
        default=600,
        description="The timeout for the simulation run. Simulation terminated if timeout time is exceeded.",
    )

    run_number: int = Field(
        default=1,
        alias="RUN",
        validation_alias="run_number",
        description="The run_number is used as extension for all generated output files.",
    )

    generator_id: str = Field(
        default="YYYY-MM-DD-HH-MM-SS-UUUUUUUU",
        description="Identifier of a particle distribution generated with the /generate endpoint of this API.",
    )

    @computed_field(
        description="Name of the file containing the initial particle distribution to be used.",
        repr=True,
    )
    @property
    def Distribution(self) -> str:
        # name initial particle distribution file in the same convention as the run output files
        # see manual of ASTRA v3.2 (Mach 2017) chapter 2
        return f"run.{0:04d}.{self.run_number:03d}"

    bunch_charge: float | None = Field(
        default=None,
        alias="Qbunch",
        validation_alias="bunch_charge",
        description="Bunch charge in [nC]. Scaling is active if bunch_charge != 0.",
        json_schema_extra={"format": "Unit: [nC]"},
    )
    schottky_coefficient: float = Field(
        default=0.0,
        alias="Q_Schottky",
        validation_alias="schottky_coefficient",
        description="Linear variation of the bunch charge with the field on the cathode. Scaling is \
                     active if Q_Schottky != 0.",
        json_schema_extra={"format": "Unit: [nC*m/MV]"},
    )
    rms_laser_spot_size: float = Field(
        default=-1.0,
        alias="XYrms",
        validation_alias="rms_laser_spot_size",
        description="Horizontal and vertical rms beam size. Scaling is active if rms_laser_spot_size > 0.0.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    rms_emission_time: float = Field(
        default=-1.0,
        alias="Trms",
        validation_alias="rms_emission_time",
        description="RMS emission time of the bunch. Scaling is active if rms_emission_time > 0.0.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    start_time: float = Field(
        default=0.0,
        alias="H_min",
        validation_alias="start_time",
        description="Minimum time step for the Runge-Kutta integration and min. time step for the \
                     space charge calculation.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    end_time: float = Field(
        default=0.001,
        alias="H_max",
        validation_alias="end_time",
        description="Maximum time step for the Runge-Kutta integration.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    max_iteration: int = Field(
        default=100000,
        alias="Max_step",
        validation_alias="max_iteration",
        description="Safety termination: after Max_step Runge_Kutta steps the run is terminated.",
    )
    z_cathode: float = Field(
        default=0.0,
        alias="Z_Cathode",
        validation_alias="z_cathode",
        description="Position of the cathode for the calculation of the mirror charge.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    track_all_particles: bool = Field(
        default=True,
        alias="Track_All",
        validation_alias="track_all_particles",
        description="If false, only the reference particle will be tracked.",
    )
    auto_phase: bool = Field(
        default=True,
        alias="Auto_Phase",
        validation_alias="auto_phase",
        description="If true, the RF phases will be set relative to the phase with maximum energy gain.",
    )

    def to_ini(self):
        return "&NEWRUN" + self._to_ini() + "/"
