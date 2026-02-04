from astra_web.schemas.table import Table
from pydantic import ConfigDict, Field


class ParticleStatistics(Table):
    """
    Table of particle statistics parameters  (including Twiss/Courant-Snyder parameters) along the beamline.

    Note: These parameters are intended to be calculated from particle distributions via openPMD beamphysics. Obtaining these values may require to load the entire particle distributions from the simulation output, which can be time-consuming.

    """

    model_config = ConfigDict(extra="forbid")

    particles_total: list[int] = Field(
        description="Number of particles in the distribution.",
    )
    particles_alive: list[int] = Field(
        description="Number of alive particles in the distribution.",
    )
    particles_dead: list[int] = Field(
        description="Number of dead particles in the distribution.",
    )

    sum_charge: list[float] = Field(
        description="Total charge of the particles in the distribution.",
        json_schema_extra={"unit": "C"},
    )

    # position
    mean_x: list[float] = Field(
        description="Mean position in the x direction.",
        json_schema_extra={"unit": "m"},
    )
    mean_y: list[float] = Field(
        description="Mean position in the y direction.",
        json_schema_extra={"unit": "m"},
    )
    mean_z: list[float] = Field(
        description="Mean position in the z direction.",
        json_schema_extra={"unit": "m"},
    )
    std_x: list[float] = Field(
        description="Standard deviation of position in the x direction.",
        json_schema_extra={"unit": "m"},
    )
    std_y: list[float] = Field(
        description="Standard deviation of position in the y direction.",
        json_schema_extra={"unit": "m"},
    )
    std_z: list[float] = Field(
        description="Standard deviation of position in the z direction.",
        json_schema_extra={"unit": "m"},
    )

    # momentum
    mean_p: list[float] = Field(
        description="Mean momentum.",
        json_schema_extra={"unit": "eV/c"},
    )
    std_p: list[float] = Field(
        description="Standard deviation of momentum.",
        json_schema_extra={"unit": "eV/c"},
    )
    mean_px: list[float] = Field(
        description="Mean momentum in the x direction.",
        json_schema_extra={"unit": "eV/c"},
    )
    mean_py: list[float] = Field(
        description="Mean momentum in the y direction.",
        json_schema_extra={"unit": "eV/c"},
    )
    mean_pz: list[float] = Field(
        description="Mean momentum in the z direction.",
        json_schema_extra={"unit": "eV/c"},
    )
    std_px: list[float] = Field(
        description="Standard deviation of momentum in the x direction.",
        json_schema_extra={"unit": "eV/c"},
    )
    std_py: list[float] = Field(
        description="Standard deviation of momentum in the y direction.",
        json_schema_extra={"unit": "eV/c"},
    )
    std_pz: list[float] = Field(
        description="Standard deviation of momentum in the z direction.",
        json_schema_extra={"unit": "eV/c"},
    )

    # energy
    mean_energy: list[float] = Field(
        description="Mean energy.",
        json_schema_extra={"unit": "eV"},
    )
    std_energy: list[float] = Field(
        description="Standard deviation of energy.",
        json_schema_extra={"unit": "eV"},
    )
    mean_kinetic_energy: list[float] = Field(
        description="Mean kinetic energy.",
        json_schema_extra={"unit": "eV"},
    )
    std_kinetic_energy: list[float] = Field(
        description="Standard deviation of kinetic energy.",
        json_schema_extra={"unit": "eV"},
    )

    # relativistic factors
    mean_gamma: list[float] = Field(
        description="Mean Lorentz factor gamma.",
    )
    std_gamma: list[float] = Field(
        description="Standard deviation of Lorentz factor gamma.",
    )
    mean_beta: list[float] = Field(
        description="Mean relativistic beta.",
    )
    std_beta: list[float] = Field(
        description="Standard deviation of relativistic beta.",
    )
    mean_beta_x: list[float] = Field(
        description="Mean relativistic beta in the x direction.",
    )
    mean_beta_y: list[float] = Field(
        description="Mean relativistic beta in the y direction.",
    )
    mean_beta_z: list[float] = Field(
        description="Mean relativistic beta in the z direction.",
    )
    std_beta_x: list[float] = Field(
        description="Standard deviation of relativistic beta in the x direction.",
    )
    std_beta_y: list[float] = Field(
        description="Standard deviation of relativistic beta in the y direction.",
    )
    std_beta_z: list[float] = Field(
        description="Standard deviation of relativistic beta in the z direction.",
    )

    # emittance
    norm_emit_x: list[float] = Field(
        description="Normalized projected emittance in the x direction.",
        json_schema_extra={"unit": "m rad"},
    )
    norm_emit_y: list[float] = Field(
        description="Normalized projected emittance in the y direction.",
        json_schema_extra={"unit": "m rad"},
    )
    norm_emit_4d: list[float] = Field(
        description="Normalized 4D emittance.",
        json_schema_extra={"unit": "m rad"},
    )

    # Twiss
    twiss_fraction: float = Field(
        description="Fraction of particles used for the calculation of the Twiss parameters and (some) emittances.",
    )

    twiss_alpha_x: list[float] = Field(
        description="Twiss parameter alpha in the x direction.",
    )
    twiss_beta_x: list[float] = Field(
        description="Twiss parameter beta in the x direction.",
    )
    twiss_gamma_x: list[float] = Field(
        description="Twiss parameter gamma in the x direction.",
    )
    twiss_emit_x: list[float] = Field(
        description="Projected emittance in the x direction.",
    )
    twiss_eta_x: list[float] = Field(
        description="Dispersion in the x direction.",
    )
    twiss_etap_x: list[float] = Field(
        description="Derivative of dispersion in the x direction.",
    )
    twiss_norm_emit_x: list[float] = Field(
        description="Normalized projected emittance in the x direction.",
    )
    twiss_alpha_y: list[float] = Field(
        description="Twiss parameter alpha in the y direction.",
    )
    twiss_beta_y: list[float] = Field(
        description="Twiss parameter beta in the y direction.",
    )
    twiss_gamma_y: list[float] = Field(
        description="Twiss parameter gamma in the y direction.",
    )
    twiss_emit_y: list[float] = Field(
        description="Projected emittance in the y direction.",
    )
    twiss_eta_y: list[float] = Field(
        description="Dispersion in the y direction.",
    )
    twiss_etap_y: list[float] = Field(
        description="Derivative of dispersion in the y direction.",
    )
    twiss_norm_emit_y: list[float] = Field(
        description="Normalized projected emittance in the y direction.",
    )
