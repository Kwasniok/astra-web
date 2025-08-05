from typing import Any
import os
from fastapi import FastAPI, Depends, Query, HTTPException, status
from fastapi.responses import ORJSONResponse
from .host_localizer import (
    Hosts,
    HostLocalizerTypes,
    LocalHostLocalizer,
    SLURMHostLocalizer,
)
from .auth.auth_schemes import api_key_auth
from .generator.schemas.particles import Particles
from .generator.schemas.io import (
    GeneratorInput,
    GeneratorDispatchOutput,
    GeneratorCompleteData,
)
from .simulation.schemas.io import (
    SimulationInput,
    SimulationAllData,
    SimulationDispatchOutput,
    StatisticsInput,
    StatisticsOutput,
)
from .generator.host_localized import (
    dispatch_particle_distribution_generation,
    load_generator_data,
    list_generator_ids,
    delete_particle_distribution,
    write_particle_distribution,
)
from .simulation.host_localized import (
    dispatch_simulation_run,
    load_simulation_data,
    list_simulation_ids,
    delete_simulation,
    get_statistics,
)
from .choices import ListCategory


tags_metadata = [
    {
        "name": "particles",
        "description": "All CRUD methods for particle distributions. Distributions are generated \
                                         by ASTRA generator binary.",
    },
    {
        "name": "simulations",
        "description": "All CRUD methods for beam dynamics simulations. Simulations are run \
                                           by ASTRA binary.",
    },
    {
        "name": "slurm",
        "description": "Configure and diagnose the SLURM backend.",
    },
]


app = FastAPI(
    title="ASTRA WebAPI",
    description="This is an API wrapper for the ASTRA simulation code developed \
                 by K. Floettmann at DESY Hamburg. For more information, refer to the official \
                 [website](https://www.desy.de/~mpyflo/).",
    contact={
        "name": "Jens Kwasniok",
        "email": "jens.kwasniok@desy.de",
    },
    root_path=os.getenv("SERVER_ROOT_PATH", ""),
    openapi_tags=tags_metadata,
    default_response_class=ORJSONResponse,
)


@app.get(
    "/particles/ids",
    dependencies=[Depends(api_key_auth)],
    tags=["particles"],
)
def list_particle_distribution_ids(
    filter: ListCategory = Query(default=ListCategory.FINISHED),
) -> list[str]:
    """
    Returns a list of particle distribution IDs.
    """
    localizer = LocalHostLocalizer.instance()
    return list_generator_ids(localizer, filter=filter)


@app.post(
    "/particles",
    dependencies=[Depends(api_key_auth)],
    tags=["particles"],
)
async def dispatch_particle_distribution_generation_(
    generator_input: GeneratorInput,
    host: Hosts = Query(default=Hosts.LOCAL),
) -> GeneratorDispatchOutput:
    local_localizer = LocalHostLocalizer.instance()
    host_localizer = HostLocalizerTypes.get_localizer(host)
    return dispatch_particle_distribution_generation(
        generator_input, local_localizer, host_localizer
    )


@app.put(
    "/particles",
    dependencies=[Depends(api_key_auth)],
    tags=["particles"],
)
def upload_particle_distribution(data: Particles) -> dict:
    localizer = LocalHostLocalizer.instance()
    gen_id = write_particle_distribution(data, localizer)
    return {"gen_id": gen_id}


@app.get(
    "/particles/{gen_id}",
    dependencies=[Depends(api_key_auth)],
    tags=["particles"],
)
def download_generator_results(gen_id: str) -> GeneratorCompleteData:
    localizer = LocalHostLocalizer.instance()
    output = load_generator_data(gen_id, localizer)
    if output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generator output for '{gen_id}' not found.",
        )
    return output


@app.delete(
    "/particles/{gen_id}",
    dependencies=[Depends(api_key_auth)],
    tags=["particles"],
)
async def delete_particle_distribution_(gen_id: str) -> None:
    localizer = LocalHostLocalizer.instance()
    blocking_links = delete_particle_distribution(gen_id, localizer)
    if blocking_links is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Particle distribution '{gen_id}' cannot be deleted because it is referenced by: {blocking_links}",
        )


@app.get(
    "/simulations/ids",
    dependencies=[Depends(api_key_auth)],
    tags=["simulations"],
)
def list_simulation_ids_(
    filter: ListCategory = Query(default=ListCategory.FINISHED),
) -> list[str]:
    """
    Returns a list of  simulation IDs.
    """
    localizer = LocalHostLocalizer.instance()
    return list_simulation_ids(localizer, filter=filter)


@app.post(
    "/simulations",
    dependencies=[Depends(api_key_auth)],
    tags=["simulations"],
)
async def dispatch_simulation(
    simulation_input: SimulationInput,
    host: Hosts = Query(default=Hosts.LOCAL),
) -> SimulationDispatchOutput:
    # local
    local_localizer = LocalHostLocalizer.instance()
    host_localizer = HostLocalizerTypes.get_localizer(host)
    return dispatch_simulation_run(simulation_input, local_localizer, host_localizer)


@app.get(
    "/simulations/{sim_id}",
    dependencies=[Depends(api_key_auth)],
    tags=["simulations"],
)
def download_simulation_data(sim_id: str) -> SimulationAllData:
    """
    Returns the output of a specific ASTRA simulation on the requested server depending
    on the given ID.
    """
    localizer = LocalHostLocalizer.instance()
    output = load_simulation_data(sim_id, localizer)
    if output is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation '{sim_id}' not found.",
        )
    else:
        return output


@app.delete(
    "/simulations/{sim_id}",
    dependencies=[Depends(api_key_auth)],
    tags=["simulations"],
)
async def delete_simulation_(sim_id: str) -> None:
    localizer = LocalHostLocalizer.instance()
    return delete_simulation(sim_id, localizer)


@app.get(
    "/simulations/{sim_id}/statistics",
    dependencies=[Depends(api_key_auth)],
    tags=["simulations"],
)
async def statistics(data: StatisticsInput, sim_id: str) -> StatisticsOutput:
    localizer = LocalHostLocalizer.instance()
    stats = get_statistics(sim_id, localizer)
    if stats is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation data for '{sim_id}' not found.",
        )
    return stats


@app.put(
    "/slurm/configure",
    dependencies=[Depends(api_key_auth)],
    tags=["slurm"],
)
async def configure_slurm(user: str, token: str) -> dict[str, Any]:
    slurm_localizer = SLURMHostLocalizer.instance()
    slurm_localizer.configure(user, token)
    return slurm_localizer.configuration


@app.get(
    "/slurm/ping",
    dependencies=[Depends(api_key_auth)],
    tags=["slurm"],
)
async def ping_slurm() -> dict[str, Any]:
    slurm_localizer = SLURMHostLocalizer.instance()
    try:
        return slurm_localizer.ping()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


@app.get(
    "/slurm/diagnose",
    dependencies=[Depends(api_key_auth)],
    tags=["slurm"],
)
async def diagnose_slurm() -> dict[str, Any]:
    slurm_localizer = SLURMHostLocalizer.instance()
    try:
        return slurm_localizer.diagnose()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
