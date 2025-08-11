import numpy as np
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from astra_web.generator.schemas.particles import Particles
from astra_web.host_localizer.schemas.dispatch import DispatchResponse
from astra_web.uuid import get_uuid
from astra_web.file import IniExportableModel
from .run import SimulationRunSpecifications
from .modules import Solenoid, Cavity
from .space_charge import SpaceCharge
from .emittance_table import XYEmittanceTable, ZEmittanceTable


class SimulationOutputSpecification(IniExportableModel):

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


class SimulationInput(IniExportableModel):

    _id: str

    # web exclusive fields:
    @property
    def id(self):
        return self._id

    comment: str | None = Field(
        default=None,
        description="Optional comment for the simulation.",
    )

    @property
    def run_dir(self) -> str:
        return self.id

    @property
    def field_file_names(self) -> set[str]:
        """
        Returns a set of all field file names used in the simulation.
        """
        return {c.field_file_name for c in self.cavities} | {
            s.field_file_name for s in self.solenoids
        }

    def excluded_ini_fields(self) -> set[str]:
        return {"id", "comment", "run_dir", "field_file_names"}

    # ASTRA fields:
    run_specs: SimulationRunSpecifications = Field(
        default=SimulationRunSpecifications(),
        description="Specifications of operative run parameters such as thread numbers, run directories and more.",
    )
    output_specs: SimulationOutputSpecification = Field(
        default=SimulationOutputSpecification(),
        description="Specifications about the output files generated by the simulation.",
    )
    cavities: list[Cavity] = Field(
        default=[],
        description="Specifications of cavities existing in the simulation setup. If not specified differently, \
            cavities will be ordered w.r.t. to the z_0 parameter values.",
    )
    solenoids: list[Solenoid] = Field(
        default=[],
        description="Specifications of solenoids existing in the simulation setup. If not specified differently, \
            solenoids will be ordered w.r.t. to the z_0 parameter values.",
    )
    space_charge: SpaceCharge = Field(default=SpaceCharge(), description="")

    def _sort_and_set_ids(self, attribute_key: str) -> None:
        attr = getattr(self, attribute_key)
        if not np.any(list(map(lambda o: o.z_0 is None, attr))):
            setattr(self, attribute_key, sorted(attr, key=lambda element: element.z_0))
        for idx, element in enumerate(getattr(self, attribute_key), start=1):
            element.id = idx

    def model_post_init(self, __context) -> None:
        self._id = get_uuid()
        self._sort_and_set_ids("cavities")
        self._sort_and_set_ids("solenoids")

    def to_ini(self) -> str:
        has_cavities = str(len(self.cavities) > 0).lower()
        has_solenoids = str(len(self.solenoids) > 0).lower()
        cavity_str = f"&CAVITY\n    LEfield = {has_cavities}\n{''.join([c.to_ini() for c in self.cavities])}/"
        solenoid_str = f"&SOLENOID\n    LBfield = {has_solenoids}\n{''.join([s.to_ini() for s in self.solenoids])}/"
        run_str = self.run_specs.to_ini()
        charge_str = self.space_charge.to_ini()
        output_str = self.output_specs.to_ini()

        return (
            "\n\n".join([run_str, output_str, charge_str, cavity_str, solenoid_str])
            + "\n"
        )


class SimulationDispatchOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sim_id: str
    dispatch_response: DispatchResponse


class SimulationData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    particles: Optional[list[Particles]] = Field(default=[Particles()])
    final_particle_counts: dict[str, int] = Field(
        description="Number of particles - active, inactive, total."
    )
    emittance_x: Optional[XYEmittanceTable] = Field(
        default=None,
    )
    emittance_y: Optional[XYEmittanceTable] = Field(
        default=None,
    )
    emittance_z: Optional[ZEmittanceTable] = Field(default=None)


class SimulationAllData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    web_input: SimulationInput
    data: SimulationData | None = Field(
        default=None,
        description="Simulation data, if the simulation has finished successfully.",
    )
    run_input: str
    run: str
