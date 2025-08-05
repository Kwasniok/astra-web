import os
import glob
from shutil import rmtree
from typing import Type, TypeVar
from astra_web.simulation.schemas.io import StatisticsOutput
from astra_web.host_localizer import HostLocalizer
from astra_web.generator.schemas.particles import Particles
from .schemas.io import (
    SimulationInput,
    SimulationData,
    SimulationAllData,
    SimulationDispatchOutput,
)
from .schemas.tables import XYEmittanceTable, ZEmittanceTable
from astra_web.file import write_txt, read_txt, write_json, read_json


def dispatch_simulation_run(
    simulation_input: SimulationInput,
    local_localizer: HostLocalizer,
    host_localizer: HostLocalizer,
) -> SimulationDispatchOutput:
    """Dispatches the simulation run based on the provided simulation input.
    The simulation input is written to disk, and the run is dispatched to the appropriate host.
    """
    # local
    write_simulation_files(simulation_input, local_localizer)
    # 'remote'
    response = host_localizer.dispatch_simulation(simulation_input)
    return SimulationDispatchOutput(
        sim_id=simulation_input.run_dir,
        dispatch_response=response,
    )


def write_simulation_files(
    simulation_input: SimulationInput, localizer: HostLocalizer
) -> None:
    """
    Write the simulation input to disk, including the INI file, element files, input JSON and linking the initial parSimulationDataticle distribution.
    """
    run_path = localizer.simulation_path(simulation_input.run_dir)
    os.makedirs(run_path, exist_ok=True)
    write_json(
        simulation_input,
        localizer.simulation_path(simulation_input.run_dir, "input.json"),
    )
    write_txt(
        simulation_input.to_ini(),
        localizer.simulation_path(simulation_input.run_dir, "run.in"),
    )
    _write_element_files(simulation_input, run_path)
    _link_initial_particle_distribution(simulation_input, localizer)


def _write_element_files(simulation_input: SimulationInput, run_path: str) -> None:
    """
    Write the files of all elements in the simulation setup to disk.
    """
    for o in simulation_input.solenoids + simulation_input.cavities:
        o.write_to_csv(run_path)


def _link_initial_particle_distribution(
    simulation_input: SimulationInput, localizer: HostLocalizer
):
    # make link relative to ensure compatibility across hosts
    target = localizer.generator_path(
        simulation_input.run_specs.generator_id, "distribution.ini"
    )
    target = os.path.relpath(
        target, localizer.simulation_path(simulation_input.run_dir)
    )
    os.symlink(
        target,
        localizer.simulation_path(
            simulation_input.run_dir, simulation_input.run_specs.Distribution
        ),
    )


def load_simulation_data(
    sim_id: str, localizer: HostLocalizer
) -> SimulationAllData | None:
    """
    Loads the entire simulation data for a given simulation ID.
    Returns None if the simulation does not exist.
    """

    if not os.path.exists(localizer.simulation_path(sim_id)):
        return None

    web_input = read_json(
        SimulationInput, localizer.simulation_path(sim_id, "input.json")
    )

    emittance_x, emittance_y, emittance_z = _load_emittances(sim_id, localizer)
    particle_paths = _particle_paths(sim_id, localizer)
    particles = [Particles.read_from_csv(path) for path in particle_paths]

    data = SimulationData(
        particles=particles,
        emittance_x=emittance_x,
        emittance_y=emittance_y,
        emittance_z=emittance_z,
    )

    run_input = read_txt(localizer.simulation_path(sim_id, "run.in"))
    run_output = read_txt(localizer.simulation_path(sim_id, "run.out"))

    return SimulationAllData(
        web_input=web_input,
        data=data,
        run_input=run_input,
        run_output=run_output,
    )


def _load_emittances(
    sim_id: str, localizer: HostLocalizer
) -> tuple[XYEmittanceTable, XYEmittanceTable, ZEmittanceTable]:

    T = TypeVar("T", bound=XYEmittanceTable | ZEmittanceTable)

    def load(cls: Type[T], coordinate: str) -> T:
        path = localizer.simulation_path(sim_id, f"run.{coordinate.upper()}emit.001")
        return cls.load_from_csv(path)

    return (
        load(XYEmittanceTable, "x"),
        load(XYEmittanceTable, "y"),
        load(ZEmittanceTable, "z"),
    )


def list_finished_simulation_ids(localizer: HostLocalizer) -> list[str]:
    """
    Lists all ID of completed simulation runs.
    """
    files = glob.glob(localizer.simulation_path("*", "FINISHED"))
    files = list(map(lambda p: p.split("/")[-2], files))

    return sorted(files)


def delete_simulation(sim_id: str, localizer: HostLocalizer) -> None:
    """
    Deletes the simulation directory for a given simulation ID.
    """
    path = localizer.simulation_path(sim_id)
    if os.path.exists(path):
        rmtree(path)


def get_statistics(sim_id: str, localizer: HostLocalizer) -> StatisticsOutput | None:
    """
    Returns statistics about the simulation.
    Returns None if the simulation does not exist.
    """

    path = localizer.simulation_path(sim_id, "FINISHED")
    if not os.path.exists(path):
        return None

    particle_paths = _particle_paths(sim_id, localizer)
    if not particle_paths:
        return None
    particles = Particles.read_from_csv(particle_paths[-1])

    return StatisticsOutput(
        sim_id=sim_id,
        particle_counts={
            "total": len(particles.x),
            "active": int(sum(particles.active_particles)),
            "lost": int(sum(particles.lost_particles)),
        },
    )


def _particle_paths(id: str, localizer: HostLocalizer) -> list[str]:
    files = glob.glob(localizer.simulation_path(id, "run.*[0-9].001"))
    return sorted(
        files,
        key=lambda s: s.split(".")[1],
    )
