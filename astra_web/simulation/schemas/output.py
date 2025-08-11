from pydantic import Field
from astra_web.file import IniExportableModel


class SimulationOutputSpecification(IniExportableModel):

    # ASTA fields:
    z_start: float = Field(
        default=0.0,
        alias="ZSTART",
        validation_alias="z_start",
        description="Minimal z position for the generation of output.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    z_stop: float = Field(
        default=1.0,
        alias="ZSTOP",
        validation_alias="z_stop",
        description="Longitudinal stop position. Tracking will stop when the bunch center passes z_stop.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    emittance_checkpoint_num: int = Field(
        default=100,
        alias="Zemit",
        validation_alias="emittance_checkpoint_num",
        description="The interval z_stop - z_start is divided into emittance_checkpoint_num sub-intervals. At the end of \
                     each sub-interval statistical bunch parameters such as emittance are saved. It is advised to set \
                     a multiple of distribution_checkpoint_num as value.",
        gt=1,
    )
    distribution_checkpoint_num: int = Field(
        default=1,
        alias="Zphase",
        validation_alias="distribution_checkpoint_num",
        description="The interval z_stop - z_start is divided into emittance_checkpoint_num sub-intervals. At the end of \
                     each sub-interval a complete particle distribution is saved.",
    )
    high_resolution: bool = Field(
        default=False,
        alias="High_res",
        validation_alias="high_resolution",
        description="If true, particle distributions are saved with increased accuracy",
    )
    store_with_high_accuracy: bool = Field(
        default=False,
        alias="RefS",
        validation_alias="store_with_high_accuracy",
        description="If true, ASTRA store output of the off-axis reference trajectory, energy gain etc. at each \
                     Runge-Kutta time step.",
    )
    store_emittance: bool = Field(
        default=False,
        alias="EmitS",
        validation_alias="store_emittance",
        description="If true, output of the beam emittance and other statistical beam parameters is generated. The parameters \
                    are calculated and stored at the end of each sub-interval defined by emittance_checkpoint_num.",
    )
    store_ts_emittance: bool = Field(
        default=False,
        alias="Tr_emitS",
        validation_alias="store_ts_emittance",
        description="If true, output of the trace space beam emittance and other statistical beam parameters is \
                    generated. The parameters are calculated and stored at the end of each sub-interval defined by emittance_checkpoint_num.",
    )
    store_complete_particle: bool = Field(
        default=False,
        alias="PhaseS",
        validation_alias="store_complete_particle",
        description="If true, the complete particle distribution is saved at distribution_checkpoint_num different locations as well as at screens and wake positions.",
    )
    store_track: bool = Field(
        default=False,
        alias="TrackS",
        validation_alias="store_track",
        description="If true, the particle trajectories are tracked as probe particles with space charge fields acting on them per Runge-Kutta time step.",
    )
    store_avg_step_size: bool = Field(
        default=False,
        alias="TcheckS",
        validation_alias="store_avg_step_size",
        description="If true, the development of the average step size is stored.",
    )
    store_space_charge_field_on_cathode: bool = Field(
        default=False,
        alias="CathodeS",
        validation_alias="store_space_charge_field_on_cathode",
        description="If true, the space charge field on the cathode is stored per Runge-Kutta time step.",
    )

    def to_ini(self) -> str:
        return "&OUTPUT" + self._to_ini() + "/"
