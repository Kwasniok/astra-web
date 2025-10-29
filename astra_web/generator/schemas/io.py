from typing import Any
from pydantic import BaseModel, Field, ConfigDict, computed_field
from astra_web.file import IniExportableModel
from astra_web.host_localizer.schemas.dispatch import DispatchResponse
from astra_web.uuid import get_uuid
from .enums import Distribution, ParticleType
from .particles import Particles


class GeneratorInput(IniExportableModel):
    """
    Input for the ASTRA particle distribution `generator`.

    note: Multiple distributions per dimension are available.
          Each distribution requires only a subset of the offered parameters.
          Therefore not all parameters need to be specified.
          The exact specificatioon of each parameter and their default values can be obtained from the ASTRA manual (v3.2 pp. 93).
    """

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

    # adding distributions: skipped

    particle_count: int | None = Field(
        default=100,
        alias="IPart",
        validation_alias="particle_count",
        description="Number of particles to be generated.",
    )
    particle_type: ParticleType | None = Field(
        default=ParticleType("electrons"),
        alias="Species",
        validation_alias="particle_type",
        description="Species of particles to be generated.",
    )

    # ions: skipped

    enable_probe_particles: bool | None = Field(
        default=True,
        alias="Probe",
        validation_alias="enable_probe_particles",
        description="If true, 6 probe particles are generated.",
    )
    quasi_random: bool | None = Field(
        default=True,
        alias="Noise_reduc",
        validation_alias="quasi_random",
        description="If true, particle coordinates are generated quasi-randomly following a Hammersley sequence.",
    )
    use_time_spread: bool | None = Field(
        default=True,
        alias="Cathode",
        validation_alias="use_time_spread",
        description="If true the particles will be generated with a time spread rather than with a spread in the longitudinal position.",
    )

    # curved cathode: skipped

    save_distribution_with_high_resolution: bool | None = Field(
        default=True,  # ASTRA default: False
        alias="High_res",
        validation_alias="save_distribution_with_high_resolution",
        description="If true, the particle distribution is saved with increased accuracy.",
    )
    save_distribution_as_binary: bool | None = Field(
        default=False,
        alias="Binary",
        validation_alias="save_distribution_as_binary",
        description="If true, the particle distribution is saved as a binary file.",
    )
    total_charge: float | None = Field(
        default=1.0,
        alias="Q_total",
        validation_alias="total_charge",
        description="Total charge of the particles, equally distributed on the number of particles.",
        json_schema_extra={"format": "Unit: [nC]"},
    )
    distribution_type: str | None = Field(
        default="standard",
        alias="Type",
        validation_alias="distribution_type",
        description="Defines the type of the distribution. Valid are `standard` and `ring`.",
    )
    distribution_ring_radius: float | None = Field(
        default=None,
        alias="Rad",
        validation_alias="distribution_ring_radius",
        description="Specifies the radius of the ring distribution.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    emission_delay_time_tau: float | None = Field(
        default=None,
        alias="Tau",
        validation_alias="emission_delay_time_tau",
        description="Exponential delay time of the emission. Active if non-zero. The delay is added to any distribution in time, i.e. to any distribution starting at the cathode. Note that the delay time is random and might interfere with the quasi random nature of an input distribution.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    reference_z: float | None = Field(
        default=0.0,
        alias="Ref_zpos",
        validation_alias="reference_z",
        description="z position of the reference particle, i.e. the longitudinal bunch position.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    reference_clock: float | None = Field(
        default=0.0,
        alias="Ref_clock",
        validation_alias="reference_clock",
        description="Initial clock time of the reference particle. Can in general be set to zero.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    reference_kinetic_energy: float = Field(
        default=0.0,
        alias="Ref_Ekin",
        validation_alias="reference_kinetic_energy",
        description="initial kinetic energy of the reference particle",
        json_schema_extra={"format": "Unit: [keV]"},
    )
    dist_z: Distribution | None = Field(
        default=Distribution("uniform"),
        alias="Dist_z",
        validation_alias="dist_z",
        description="Specifies the type of the longitudinal particle distribution.",
    )
    dist_z_bunch_length_rms: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="sig_z",
        validation_alias="dist_t_bunch_length_rms",
        description="RMS value of the bunch length.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_z_gaussian_cutoff: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="C_sig_z",
        validation_alias="dist_z_gaussian_cutoff",
        description="Cuts off a Gaussian longitudinal distribution at dist_z_gaussian_cutoff times dist_z_bunch_length_rms.",
    )
    dist_z_bunch_length: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="Lz",
        validation_alias="dist_z_bunch_length",
        description="Length of the bunch.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_z_bunch_length_rise: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="rz",
        validation_alias="dist_z_bunch_length_rise",
        description="Plateau distribution only: Rising of a bunch.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_t_emission_time_rms: float | None = Field(
        default=None,  # ASTRA default: 1.0e-3
        alias="sig_clock",
        validation_alias="dist_t_emission_time_rms",
        description="RMS rms value of the emission time, i.e. the bunch length if generated from a cathode.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    dist_t_emission_time_cutoff: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="C_sig_clock",
        validation_alias="dist_t_emission_time_cutoff",
        description="Gaussian cutoff relative to dist_t_emission_time_rms.",
    )
    dist_t_emission_time: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="Lt",
        validation_alias="dist_t_emission_time",
        description="Plateau distributions only: Duration of the bunch emission.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    dist_t_emission_time_rise: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="rt",
        validation_alias="dist_t_emission_time_rise",
        description="Plateau distributions only: Rise time of the bunch emission.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    dist_pz: Distribution | None = Field(
        default=Distribution("uniform"),
        alias="Dist_pz",
        validation_alias="dist_pz",
        description="Specifies the longitudinal energy and momentum distribution, respectively.",
    )
    dist_pz_energy_spread_rms: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="sig_Ekin",
        validation_alias="dist_pz_energy_spread_rms",
        description="RMS value of the energy spread.",
        json_schema_extra={"format": "Unit: [keV]"},
    )
    dist_pz_energy_spread_gaussian_cutoff: float | None = Field(
        default=None,  # ASTRA default: 100.0
        alias="C_sig_Ekin",
        validation_alias="dist_pz_energy_spread_gaussian_cutoff",
        description="RMS value of the energy spread.",
        json_schema_extra={"format": "Unit: [keV]"},
    )
    dist_pz_energy_width: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="LE",
        validation_alias="dist_pz_energy_width",
        description="Width of the energy distribution.",
        json_schema_extra={"format": "Unit: [keV]"},
    )
    dist_pz_energy_rise: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="rE",
        validation_alias="dist_pz_energy_rise",
        description="Rising of the energy distribution.",
        json_schema_extra={"format": "Unit: [keV]"},
    )
    dist_pz_emittance: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="emit_z",
        validation_alias="dist_pz_emittance",
        description="Longitudinal particle emittance. Can be specified instead of the energy spread. If an energy spread and an emittance is specified the energy spread has priority.",
        json_schema_extra={"format": "Unit: [π keV mm]"},
    )
    dist_pz_correlated_energy_spread: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="cor_Ekin",
        validation_alias="dist_pz_correlated_energy_spread",
        description="Correlated energy spread.",
    )
    dist_pz_photon_energy: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="E_photon",
        validation_alias="dist_pz_photon_energy",
        description="Fermi-Dirac distribution only: Photon energy.",
    )
    dist_pz_phi_eff: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="phi_eff",
        validation_alias="dist_pz_phi_eff",
        description="Fermi-Dirac distribution only: Effective work function parameter.",
    )
    dist_x: Distribution | None = Field(
        default=Distribution("gauss"),
        alias="Dist_x",
        validation_alias="dist_x",
        description="Specifies the transverse particle distribution in the horizontal direction.",
    )
    dist_x_bunch_size_rms: float | None = Field(
        default=None,  # ASTRA default: 1.0
        alias="sig_x",
        validation_alias="dist_x_bunch_size_rms",
        description="RMS bunch size in the horizontal direction.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_x_bunch_size_gaussian_cutoff: float | None = Field(
        default=None,  # ASTRA default: 1.0
        alias="C_sig_x",
        validation_alias="dist_x_bunch_size_gaussian_cutoff",
        description="Cuts of at `dist_x_bunch_size_rms` times `dist_x_bunch_size_gaussian_cutoff`.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_x_bunch_width: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="Lx",
        validation_alias="dist_x_bunch_width",
        description="Width of the bunch.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_x_bunch_width_rise: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="rx",
        validation_alias="dist_x_bunch_width_rise",
        description="Plateau distributions only: Rising of the bunch width.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_x_shift: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="x_off",
        validation_alias="dist_x_shift",
        description="Horizontal offset.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_x_dispersion: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="Disp_x",
        validation_alias="dist_x_dispersion",
        description="Horizontal dispersion. A horizontal offset is added to all particles according to:  `x -> x + dist_x_dispersion * ΔP / P`. Increases the calculated bunch emittance.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_px: Distribution | None = Field(
        default=Distribution("gauss"),
        alias="Dist_px",
        validation_alias="dist_px",
        description="Specifies the transverse momentum distribution in the horizontal direction.",
    )
    dist_px_normalized_transversal_emittance: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="Nemit_x",
        validation_alias="dist_px_normalized_transversal_emittance",
        description="Normalized transverse emittance in the horizontal direction. Can be specified instead of a transverse momentum spread. If a momentum spread and an emittance is specified the emittance has priority. Also the normalized vertical emittance if `dist_px = radial`.",
        json_schema_extra={"format": "Unit: [π mrad mm]"},
    )
    dist_px_rms: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="sig_px",
        validation_alias="dist_px_rms",
        description="RMS value of the horizontal momentum distribution.",
        json_schema_extra={"format": "Unit: [eV/c]"},
    )
    dist_px_gaussian_cutoff: float | None = Field(
        default=None,  # ASTRA default: 100.0
        alias="C_sig_px",
        validation_alias="dist_px_gaussian_cutoff",
        description="Cuts off the horizontal momentum distribution at dist_px_gaussian_cutoff times dist_px_rms.",
    )
    dist_px_width: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="Lpx",
        validation_alias="dist_px_width",
        description="Plateau distribution only: Width of horizontal momentum distribution.",
        json_schema_extra={"format": "Unit: [eV/c]"},
    )
    dist_px_rise: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="rpx",
        validation_alias="dist_px_rise",
        description="Plateau distribution only: Rising.",
        json_schema_extra={"format": "Unit: [eV/c]"},
    )
    dist_px_correlation: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="cor_px",
        validation_alias="dist_px_correlation",
        description="Correlated beam divergence in the horizontal direction `-α / β[mm] * x_rms[mm]`. For extreme settings of cor_px the correlated beam divergence cannot be set correctly and the beam energy will be increased by generator. A warning will be given in this case.",
    )
    dist_y: Distribution | None = Field(
        default=Distribution("gauss"),
        alias="Dist_y",
        validation_alias="dist_y",
        description="Specifies the transverse particle distribution in the vertical direction.",
    )
    dist_y_bunch_size_rms: float | None = Field(
        default=None,  # ASTRA default: 1.0
        alias="sig_y",
        validation_alias="dist_y_bunch_size_rms",
        description="RMS bunch size in the vertical direction.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_y_bunch_size_gaussian_cutoff: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="C_sig_y",
        validation_alias="dist_y_bunch_size_gaussian_cutoff",
        description="Cuts of at `dist_y_bunch_size_rms` times `dist_y_bunch_size_gaussian_cutoff`.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_y_bunch_width: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="Ly",
        validation_alias="dist_y_bunch_width",
        description="Width of the bunch.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_y_bunch_width_rise: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="ry",
        validation_alias="dist_y_bunch_width_rise",
        description="Plateau distributions only: Rising of the bunch width.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_y_shift: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="y_off",
        validation_alias="dist_y_shift",
        description="Vertical offset.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_y_dispersion: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="Disp_y",
        validation_alias="dist_y_dispersion",
        description="Vertical dispersion. A vertical offset is added to all particles according to:  `y -> y + dist_y_dispersion * ΔP / P`. Increases the calculated bunch emittance.",
        json_schema_extra={"format": "Unit: [mm]"},
    )
    dist_py: Distribution | None = Field(
        default=Distribution("gauss"),
        alias="Dist_py",
        validation_alias="dist_py",
        description="Specifies the transverse momentum distribution in the vertical direction.",
    )
    dist_py_normalized_transversal_emittance: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="Nemit_y",
        validation_alias="dist_py_normalized_transversal_emittance",
        description="Normalized transverse emittance in the vertical direction. Can be specified instead of a transverse momentum spread. If a momentum spread and an emittance is specified the emittance has priority. Also the normalized vertical emittance if `dist_py = radial`.",
        json_schema_extra={"format": "Unit: [π mrad mm]"},
    )
    dist_py_rms: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="sig_py",
        validation_alias="dist_py_rms",
        description="RMS value of the horizontal momentum distribution.",
        json_schema_extra={"format": "Unit: [eV/c]"},
    )
    dist_py_gaussian_cutoff: float | None = Field(
        default=None,  # ASTRA default: 100.0
        alias="C_sig_py",
        validation_alias="dist_py_gaussian_cutoff",
        description="Cuts off the vertical momentum distribution at dist_py_gaussian_cutoff times dist_py_rms.",
    )
    dist_py_width: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="Lpy",
        validation_alias="dist_py_width",
        description="Plateau distribution only: Width of vertical momentum distribution.",
        json_schema_extra={"format": "Unit: [eV/c]"},
    )
    dist_py_rise: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="rpy",
        validation_alias="dist_py_rise",
        description="Plateau distribution only: Rising.",
        json_schema_extra={"format": "Unit: [eV/c]"},
    )
    dist_py_correlation: float | None = Field(
        default=None,  # ASTRA default: 0.0
        alias="cor_py",
        validation_alias="dist_py_correlation",
        description="Correlated beam divergence in the vertical direction `-α / β[mm] * y_rms[mm]`. For extreme settings of cor_py the correlated beam divergence cannot be set correctly and the beam energy will be increased by generator. A warning will be given in this case.",
    )

    def to_ini(self, indent: int = 4) -> str:
        return f"&INPUT{super().to_ini(indent=indent)}/"

    def model_post_init(self, context: Any, /) -> None:
        self._id = get_uuid()


class GeneratorDispatchOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gen_id: str
    dispatch_response: DispatchResponse


class GeneratorOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    particles: Particles


class GeneratorMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    comment: str | None = Field(
        default=None, description="Optional comment for the generator."
    )


class GeneratorData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input: GeneratorInput | None = Field(
        description="Generator input as provided by the user."
    )
    output: GeneratorOutput | None = Field(
        default=None,
        description="Generator output, if the generation has finished successfully.",
    )
    astra_input: str | None = Field(
        default=None, description="Raw input file for ASTRA generator."
    )
    astra_output: str | None = Field(
        description="Raw output file from ASTRA generator."
    )
    meta: GeneratorMeta | None = Field(
        default=None,
        description="Metadata associated with the particle distribution.",
    )
