import os, glob
from shutil import rmtree
from fastapi import FastAPI, Depends, Query, HTTPException, status
from fastapi.responses import ORJSONResponse
from .uuid import get_uuid
from .host_localizer import (
    Hosts,
    HostLocalizerTypes,
    LocalHostLocalizer,
)
from .auth.auth_schemes import api_key_auth
from .generator.schemas.particles import Particles
from .generator.schemas.io import GeneratorInput, GeneratorID, GeneratorOutput
from .simulation.schemas.io import (
    SimulationInput,
    SimulationOutput,
    SimulationID,
    StatisticsInput,
    StatisticsOutput,
)
from .host_localizer.schemas.dispatch import DispatchResponse
from .generator.host_localized import (
    write_generator_files,
    read_particle_file,
    read_generator_file,
)
from .simulation.host_localized import (
    write_simulation_files,
    load_simulation_output,
    get_statistics,
)

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
    "/particles",
    dependencies=[Depends(api_key_auth)],
    tags=["particles"],
)
def list_available_particle_distributions() -> list[str]:
    """
    Returns a list of all existing particle distributions on the requested server.
    """
    localizer = LocalHostLocalizer.instance()
    files = glob.glob(localizer.generator_path("*", ".ini"))
    files = list(map(lambda p: p.split("/")[-1].split(".ini")[0], files))

    return sorted(files)


@app.post(
    "/particles",
    dependencies=[Depends(api_key_auth)],
    tags=["particles"],
)
async def dispatch_particle_distribution_generation(
    generator_input: GeneratorInput,
    host: Hosts = Query(default=Hosts.LOCAL),
) -> GeneratorID:
    # local
    local_localizer = LocalHostLocalizer.instance()
    write_generator_files(generator_input, local_localizer)
    # 'remote'
    host_localizer = HostLocalizerTypes.get_localizer(host)
    host_localizer.dispatch_generation(generator_input)
    return GeneratorID(gen_id=generator_input.gen_id)


@app.put(
    "/particles/{gen_id}",
    dependencies=[Depends(api_key_auth)],
    tags=["particles"],
)
def upload_particle_distribution(data: Particles, gen_id: str | None = None) -> dict:
    localizer = LocalHostLocalizer.instance()
    if gen_id is None:
        gen_id = get_uuid()
    path = localizer.generator_path(gen_id, ".ini")
    if os.path.exists(path):
        os.remove(path)

    data.to_csv(path)
    return {"gen_id": gen_id}


@app.get(
    "/particles/{gen_id}",
    dependencies=[Depends(api_key_auth)],
    tags=["particles"],
)
def download_generator_results(gen_id: str) -> GeneratorOutput:
    localizer = LocalHostLocalizer.instance()
    path = localizer.generator_path(gen_id, ".ini")
    if not os.path.exists(path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generator output for '{gen_id}' not found.",
        )
    return GeneratorOutput(
        gen_id=gen_id,
        particles=read_particle_file(gen_id, localizer),
        input_ini=read_generator_file(gen_id, ".in", localizer),
        run_output=read_generator_file(gen_id, ".out", localizer),
    )


@app.delete(
    "/particles/{gen_id}",
    dependencies=[Depends(api_key_auth)],
    tags=["particles"],
)
async def delete_particle_distribution(gen_id: str) -> None:
    localizer = LocalHostLocalizer.instance()
    path = localizer.generator_path(gen_id, ".ini")
    if os.path.exists(path):
        os.remove(path)


@app.get(
    "/simulations",
    dependencies=[Depends(api_key_auth)],
    tags=["simulations"],
)
def list_available_particle_distributions() -> list[str]:
    """
    Returns a list of all existing simulations on the requested server.
    """
    localizer = LocalHostLocalizer.instance()
    files = glob.glob(localizer.simulation_path("*"))
    files = list(map(lambda p: p.split("/")[-1], files))

    return sorted(files)


@app.post(
    "/simulations",
    dependencies=[Depends(api_key_auth)],
    tags=["simulations"],
)
async def dispatch_simulation(
    simulation_input: SimulationInput,
    host: Hosts = Query(default=Hosts.LOCAL),
) -> SimulationID:
    # local
    local_localizer = LocalHostLocalizer.instance()
    write_simulation_files(simulation_input, local_localizer)
    # 'remote'
    host_localizer = HostLocalizerTypes.get_localizer(host)
    host_localizer.dispatch_simulation(simulation_input)
    return SimulationID(sim_id=simulation_input.sim_id)


@app.get(
    "/simulations/{sim_id}",
    dependencies=[Depends(api_key_auth)],
    tags=["simulations"],
)
def download_simulation_results(sim_id: str) -> SimulationOutput:
    """
    Returns the output of a specific ASTRA simulation on the requested server depending
    on the given ID.
    """
    localizer = LocalHostLocalizer.instance()
    output = load_simulation_output(sim_id, localizer)
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
async def delete_simulation(sim_id: str) -> None:
    localizer = LocalHostLocalizer.instance()
    path = localizer.simulation_path(sim_id)
    if os.path.exists(path):
        rmtree(path)


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
            detail=f"Simulation '{sim_id}' not found.",
        )
    return stats
