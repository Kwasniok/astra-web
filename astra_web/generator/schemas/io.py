from typing import Any
from pydantic import BaseModel, Field, ConfigDict, computed_field
from astra_web.file import IniExportableModel
from astra_web.host_localizer.schemas.dispatch import DispatchResponse
from astra_web.uuid import get_uuid
from .enums import Distribution, ParticleType
from .particles import Particles


class GeneratorInput(IniExportableModel):

    _id: str

    # web exclusive fields:
    @property
    def id(self):
        return self._id

    comment: str | None = Field(
        default=None,
        description="Optional comment for the particle generation.",
    )

    def excluded_ini_fields(self) -> set[str]:
        return {"id", "comment"}

    # ASTRA fields:
    @computed_field
    @property
    def FNAME(self) -> str:
        return "distribution.ini"

    Add: bool | None = False
    N_add: int | None = 0
    particle_count: int = Field(
        default=100,
        alias="IPart",
        validation_alias="particle_count",
        description="Number of particles to be generated.",
    )
    particle_type: ParticleType = Field(
        default=ParticleType("electrons"),
        alias="Species",
        validation_alias="particle_type",
        description="Species of particles to be generated.",
    )
    generate_probe_particles: bool = Field(
        default=True,
        alias="Probe",
        validation_alias="generate_probe_particles",
        description="If true, 6 probe particles are generated.",
    )
    quasi_random: bool = Field(
        default=True,
        alias="Noise_reduc",
        validation_alias="quasi_random",
        description="If true, particle coordinates are generated quasi-randomly following a Hammersley sequence.",
    )
    time_spread: bool = Field(
        default=True,
        alias="Cathode",
        validation_alias="time_spread",
        description="If true the particles will be generated with a time spread rather than with a \
                     spread in the longitudinal position.",
    )
    high_accuracy: bool = Field(
        default=True,
        alias="High_res",
        validation_alias="high_accuracy",
        description="If true, the particle distribution is saved with increased accuracy.",
    )
    total_charge: float = Field(
        default=1.0,
        alias="Q_total",
        validation_alias="total_charge",
        description="Total charge of the particles, equally distributed on the number of particles.",
        json_schema_extra={"format": "Unit: [nC]"},
    )
    dist_z: Distribution = Field(
        default=Distribution("gauss"),
        alias="Dist_z",
        validation_alias="dist_z",
        description="Specifies the type of the longitudinal particle distribution.",
    )
    dist_pz: Distribution = Field(
        default=Distribution("gauss"),
        alias="Dist_pz",
        validation_alias="dist_pz",
        description="Specifies the longitudinal energy and momentum distribution, respectively.",
    )
    dist_x: Distribution = Field(
        default=Distribution("gauss"),
        alias="Dist_x",
        validation_alias="dist_x",
        description="Specifies the transverse particle distribution in the horizontal direction.",
    )
    dist_px: Distribution = Field(
        default=Distribution("gauss"),
        alias="Dist_px",
        validation_alias="dist_px",
        description="Specifies the transverse momentum distribution in the horizontal direction.",
    )
    dist_y: Distribution = Field(
        default=Distribution("gauss"),
        alias="Dist_y",
        validation_alias="dist_y",
        description="Specifies the transverse particle distribution in the vertical direction.",
    )
    dist_py: Distribution = Field(
        default=Distribution("gauss"),
        alias="Dist_py",
        validation_alias="dist_py",
        description="Specifies the transverse momentum distribution in the vertical direction.",
    )
    cor_energy_spread: float = Field(
        default=0.0,
        alias="cor_Ekin",
        validation_alias="cor_energy_spread",
        description="Correlated energy spread.",
    )
    cor_px: float = Field(
        default=0.0,
        description="correlated beam divergence in the horizontal direction.",
        json_schema_extra={"format": "Unit: [mrad]"},
    )
    cor_py: float = Field(
        default=0.0,
        description="Correlated beam divergence in the vertical direction.",
        json_schema_extra={"format": "Unit: [mrad]"},
    )
    reference_kinetic_energy: float = Field(
        default=0.0,
        alias="Ref_Ekin",
        validation_alias="reference_kinetic_energy",
        description="initial kinetic energy of the reference particle",
        json_schema_extra={"format": "Unit: [keV]"},
    )
    z_0_ref: float = Field(
        default=0.0,
        alias="Ref_zpos",
        validation_alias="z_0_ref",
        description="z position of the reference particle, i.e. the longitudinal bunch position.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    rms_energy_spread: float | None = Field(
        default=None,
        alias="sig_Ekin",
        validation_alias="rms_energy_spread",
        description="RMS value of the energy spread.",
        json_schema_extra={"format": "Unit: [keV]"},
    )
    rms_bunch_size_x: float = Field(
        default=1.0,
        alias="sig_x",
        validation_alias="rms_bunch_size_x",
        description="RMS bunch size in the horizontal direction.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    rms_dist_px: float | None = Field(
        default=None,
        alias="sig_px",
        validation_alias="rms_dist_px",
        description="RMS value of the horizontal momentum distribution.",
        json_schema_extra={"format": "Unit: [eV/c]"},
    )
    rms_bunch_size_y: float | None = Field(
        default=None,
        alias="sig_y",
        validation_alias="rms_bunch_size_y",
        description="RMS bunch size in the vertical direction.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    rms_dist_py: float | None = Field(
        default=None,
        alias="sig_py",
        validation_alias="rms_dist_py",
        description="RMS value of the vertical momentum distribution.",
        json_schema_extra={"format": "Unit: [eV/c]"},
    )
    rms_bunch_size_z: float | None = Field(
        default=None,
        alias="sig_z",
        validation_alias="rms_bunch_size_z",
        description="RMS value of the bunch length.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    sig_t: float | None = Field(
        default=None,
        alias="sig_clock",
        validation_alias="sig_t",
        description="RMS rms value of the emission time, i.e. the bunch length if generated from a cathode.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    x_emittance: float | None = Field(
        default=None,
        alias="Nemit_x",
        validation_alias="x_emittance",
        description="Normalized transverse emittance in the horizontal direction.",
        json_schema_extra={"format": "Unit: [pi*mrad*mm]"},
    )
    y_emittance: float | None = Field(
        default=None,
        alias="Nemit_y",
        validation_alias="y_emittance",
        description="Normalized transverse emittance in the vertical direction.",
        json_schema_extra={"format": "Unit: [pi*mrad*mm]"},
    )
    gaussian_cutoff_x: float | None = Field(
        default=None,
        alias="C_sig_x",
        validation_alias="gaussian_cutoff_x",
        description="Cuts off a Gaussian longitudinal distribution at C_sig_z times sig_z.",
    )
    gaussian_cutoff_y: float | None = Field(
        default=None,
        alias="C_sig_y",
        validation_alias="gaussian_cutoff_y",
        description="Cuts off a Gaussian longitudinal distribution at C_sig_z times sig_z.",
    )
    gaussian_cutoff_z: float | None = Field(
        default=None,
        alias="C_sig_z",
        validation_alias="gaussian_cutoff_z",
        description="Cuts off a Gaussian longitudinal distribution at C_sig_z times sig_z.",
    )
    flattop_z_length: float | None = Field(
        default=None,
        alias="Lz",
        validation_alias="flattop_z_length",
        description="Length of the bunch.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    flattop_rise_z: float | None = Field(
        default=None,
        alias="rz",
        validation_alias="flattop_rise_z",
        description="Rise time of a bunch with flattop distribution.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    flattop_time_length: float | None = Field(
        default=None,
        alias="Lt",
        validation_alias="flattop_time_length",
        description="Length of the bunch with flattop distribution.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    flattop_rise_time: float | None = Field(
        default=None,
        alias="rt",
        validation_alias="flattop_rise_time",
        description="Rise time of a bunch with flattop distribution.",
        json_schema_extra={"format": "Unit: [ns]"},
    )

    def to_ini(self, indent: int = 4) -> str:
        return f"&INPUT{super().to_ini(indent=indent)}/"

    def model_post_init(self, context: Any, /) -> None:
        self._id = get_uuid()


class GeneratorDispatchOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gen_id: str
    dispatch_response: DispatchResponse


class GeneratorData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    particles: Particles


class GeneratorCompleteData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    web_input: GeneratorInput
    data: GeneratorData | None = Field(
        default=None,
        description="Generator data, if the generation has finished successfully.",
    )
    generator_input: str
    generator_output: str
