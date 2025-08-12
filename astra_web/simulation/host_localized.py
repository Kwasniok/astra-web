import os
import re
import glob
from shutil import rmtree
from typing import Type, TypeVar
from datetime import datetime
from astra_web.host_localizer import HostLocalizer
from astra_web.generator.schemas.particles import Particles
from .schemas.io import (
    SimulationInput,
    SimulationData,
    SimulationMetaData,
    SimulationAllData,
    SimulationDispatchOutput,
)
from .schemas.emittance_table import XYEmittanceTable, ZEmittanceTable
from astra_web.file import write_txt, read_txt, write_json, read_json
from astra_web.choices import ListDispatchedCategory


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
    _link_initial_particle_distribution(simulation_input, localizer)
    _link_field_files(simulation_input, localizer)


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


def _link_field_files(simulation_input: SimulationInput, localizer: HostLocalizer):
    for file_name in simulation_input.field_file_names:
        _link_field_file(file_name, simulation_input.run_dir, localizer)


def _link_field_file(file_name: str, run_dir: str, localizer: HostLocalizer):
    # make link relative to ensure compatibility across hosts
    target = localizer.field_path(file_name)
    target = os.path.relpath(target, localizer.simulation_path(run_dir))
    os.symlink(target, localizer.simulation_path(run_dir, file_name))


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

    particle_paths = _particle_paths(sim_id, localizer)
    particles = [Particles.read_from_csv(path) for path in particle_paths]
    final_particle_counts = {
        "total": len(particles[-1].x),
        "active": int(sum(particles[-1].active_particles)),
        "lost": int(sum(particles[-1].lost_particles)),
    }
    try:
        emittance_x, emittance_y, emittance_z = _load_emittances(sim_id, localizer)
    except FileNotFoundError:
        emittance_x, emittance_y, emittance_z = None, None, None

    data = SimulationData(
        particles=particles,
        final_particle_counts=final_particle_counts,
        emittance_x=emittance_x,
        emittance_y=emittance_y,
        emittance_z=emittance_z,
    )

    run_input = read_txt(localizer.simulation_path(sim_id, "run.in"))
    run_output = read_txt(localizer.simulation_path(sim_id, "run.out"))
    meta = _extract_run_output_meta_data(run_output)

    return SimulationAllData(
        web_input=web_input,
        data=data,
        run_input=run_input,
        run_output=run_output,
        meta=meta,
    )


def _load_emittances(
    sim_id: str, localizer: HostLocalizer
) -> tuple[XYEmittanceTable | None, XYEmittanceTable | None, ZEmittanceTable | None]:

    T = TypeVar("T", bound=XYEmittanceTable | ZEmittanceTable)

    def load(cls: Type[T], coordinate: str) -> T | None:
        path = localizer.simulation_path(sim_id, f"run.{coordinate.upper()}emit.001")
        try:
            return cls.read_from_csv(path)
        except FileNotFoundError:
            return None

    return (
        load(XYEmittanceTable, "x"),
        load(XYEmittanceTable, "y"),
        load(ZEmittanceTable, "z"),
    )


def _extract_run_output_meta_data(
    run_output: str,
) -> SimulationMetaData:
    finished_date = None
    execution_time = None

    for line in run_output.splitlines():
        if "finished simulation" in line:
            date_match = re.search(
                r"(\d{1,2})\.\s*(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})", line
            )
            if date_match:
                day, month, year, hour, minute = map(int, date_match.groups())
                finished_date = datetime(year, month, day, hour, minute)
        elif "execution time" in line:
            time_match = re.search(r"(\d+)\s*min\s*([\d.]+)\s*sec", line)
            if time_match:
                minutes = int(time_match.group(1))
                seconds = float(time_match.group(2))
                execution_time = minutes * 60 + seconds

    return SimulationMetaData(
        finished_date=finished_date,
        execution_time=execution_time,
    )


def list_simulation_ids(
    localizer: HostLocalizer,
    filter: ListDispatchedCategory,
) -> list[str]:
    """
    Lists IDs of simulations.
    """
    ids_all = map(
        lambda p: os.path.split(p)[-1],
        glob.glob(localizer.simulation_path("*")),
    )
    ids_finished = (id for id in ids_all if _is_finished(id, localizer))
    ids_pending = (id for id in ids_all if not _is_finished(id, localizer))

    match filter:
        case ListDispatchedCategory.ALL:
            return sorted(ids_all)
        case ListDispatchedCategory.FINISHED:
            return sorted(ids_finished)
        case ListDispatchedCategory.PENDING:
            return sorted(ids_pending)


def delete_simulation(sim_id: str, localizer: HostLocalizer) -> None:
    """
    Deletes the simulation directory for a given simulation ID.
    """
    path = localizer.simulation_path(sim_id)
    if os.path.exists(path):
        rmtree(path)


def _particle_paths(id: str, localizer: HostLocalizer) -> list[str]:
    files = glob.glob(localizer.simulation_path(id, "run.*[0-9].001"))
    return sorted(
        files,
        key=lambda s: s.split(".")[1],
    )


def _is_finished(sim_id: str, localizer: HostLocalizer) -> bool:
    """
    Checks if the simulation is finished.
    """
    path = localizer.simulation_path(sim_id, "run.err")
    if os.path.exists(path):
        return False
    path = localizer.simulation_path(sim_id, "run.out")
    if os.path.exists(path):
        return "finished simulation" in read_txt(path)
    return False
