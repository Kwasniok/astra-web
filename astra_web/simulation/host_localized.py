import os
import glob
import pandas as pd
import json
from subprocess import run
from astra_web.simulation.schemas.io import StatisticsOutput
from astra_web.host_localizer import HostLocalizer
from astra_web.generator.util import _read_particle_file
from .schemas.io import SimulationInput, SimulationOutput
from .schemas.tables import XYEmittanceTable, ZEmittanceTable


def write_simulation_files(
    simulation_input: SimulationInput, localizer: HostLocalizer
) -> None:
    """
    Write the simulation input to disk, including the INI file, element files, input JSON and linking the initial particle distribution.
    """
    run_path = localizer.simulation_path(simulation_input.run_dir)
    os.makedirs(run_path, exist_ok=True)
    _write_simulation_ini(simulation_input, run_path)
    _write_element_files(simulation_input, run_path)
    _write_input_json(simulation_input, run_path)
    _link_initial_particle_distribution(simulation_input, localizer)


def _write_simulation_ini(simulation_input: SimulationInput, run_path: str) -> None:
    """
    Write the simulation INI file.
    """
    ini_string = simulation_input.to_ini()
    with open(os.path.join(run_path, "run.in"), "w") as input_file:
        input_file.write(ini_string)


def _write_element_files(simulation_input: SimulationInput, run_path: str) -> None:
    """
    Write the files of all elements in the simulation setup to disk.
    """
    for o in simulation_input.solenoids + simulation_input.cavities:
        o.write_to_disk(run_path)


def _write_input_json(simulation_input: SimulationInput, run_path: str) -> None:
    """
    Write the input parameters to a JSON file.
    """
    with open(os.path.join(run_path, "input.json"), "w") as f:
        data = {
            "solenoid_strength": simulation_input.solenoids[0].MaxB,
            "spot_size": simulation_input.run_specs.XYrms,
            "emission_time": simulation_input.run_specs.Trms,
            "gun_phase": simulation_input.cavities[0].Phi,
            "gun_gradient": simulation_input.cavities[0].MaxE,
            "generator_id": simulation_input.run_specs.generator_id,
        }
        str_ = json.dumps(
            data,
            indent=4,
            sort_keys=True,
            separators=(",", ": "),
            ensure_ascii=False,
        )
        f.write(str_)


def _link_initial_particle_distribution(
    simulation_input: SimulationInput, localizer: HostLocalizer
):
    # make link relative to ensure compatibility across hosts
    target = localizer.generator_path(simulation_input.run_specs.generator_id, ".ini")
    target = os.path.relpath(
        target, localizer.simulation_path(simulation_input.run_dir)
    )
    os.symlink(
        target,
        localizer.simulation_path(
            simulation_input.run_dir, simulation_input.run_specs.Distribution
        ),
    )


def load_simulation_output(
    sim_id: str, localizer: HostLocalizer
) -> SimulationOutput | None:
    """
    Loads the simulation output for a given simulation ID.
    Returns None if the simulation does not exist."""

    path = localizer.simulation_path(sim_id)
    if not os.path.exists(path):
        return None

    x_table, y_table, z_table = _load_emittance_output(path)
    with open(os.path.join(path, "run.out"), "r") as f:
        output = f.read()
    with open(os.path.join(path, "run.in"), "r") as f:
        input_ini = f.read()

    particle_paths = sorted(
        glob.glob(os.path.join(path, "run.*[0-9].001")), key=lambda s: s.split(".")[1]
    )
    particles = [_read_particle_file(path) for path in particle_paths]

    return SimulationOutput(
        sim_id=sim_id,
        input_ini=input_ini,
        run_output=output,
        particles=particles,
        emittance_x=x_table,
        emittance_y=y_table,
        emittance_z=z_table,
    )


def _load_emittance_output(run_dir: str) -> list[XYEmittanceTable]:
    tables = []
    for coordinate in ["x", "y", "z"]:
        file_name = os.path.join(run_dir, f"run.{coordinate.upper()}emit.001")
        model_cls = ZEmittanceTable if coordinate == "z" else XYEmittanceTable
        tables.append(_load(file_name, model_cls))

    return tables


def _load(file_path: str, model_cls):
    try:
        if os.path.exists(file_path):
            return model_cls.from_csv(file_path)
        else:
            return None
    except pd.errors.EmptyDataError:
        return None


def get_statistics(sim_id: str, localizer: HostLocalizer) -> StatisticsOutput | None:
    """
    Returns statistics about the simulation.
    Returns None if the simulation does not exist.
    """

    path = localizer.simulation_path(sim_id)
    if not os.path.exists(path):
        return None

    particles = _read_particle_file(_particle_paths(sim_id, localizer)[-1])

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
