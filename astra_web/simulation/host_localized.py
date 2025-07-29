import os
import glob
import numpy as np
import pandas as pd
import json
from subprocess import run
from pmd_beamphysics import ParticleGroup
from astra_web.generator.schemas.particles import Particles
from astra_web.simulation.schemas.io import StatisticsOutput
from astra_web.host_localizer import HostLocalizer
from astra_web.generator.util import _read_particle_file
from .schemas.io import SimulationInput, SimulationOutput
from .schemas.tables import XYEmittanceTable, ZEmittanceTable


def write_simulation_files(
    simulation_input: SimulationInput, localizer: HostLocalizer
) -> None:
    """
    Write the simulation input to disk, including the INI file, element files and input JSON.
    """
    run_path = localizer.simulation_path(simulation_input.run_dir)
    os.makedirs(run_path, exist_ok=True)
    _write_simulation_ini(simulation_input, run_path)
    _write_element_files(simulation_input, run_path)
    _write_input_json(simulation_input, run_path)


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
            "input_distribution": simulation_input.run_specs.particle_file_name,
        }
        str_ = json.dumps(
            data,
            indent=4,
            sort_keys=True,
            separators=(",", ": "),
            ensure_ascii=False,
        )
        f.write(str_)


def process_simulation_input(
    simulation_input: SimulationInput, localizer: HostLocalizer
) -> None:
    _link_initial_particle_distribution(simulation_input, localizer)
    raw_process_output = run(
        _run_command(simulation_input, localizer),
        cwd=localizer.simulation_path(simulation_input.run_dir),
        capture_output=True,
        timeout=simulation_input.run_specs.timeout,
    ).stdout

    terminal_output = raw_process_output.decode()
    output_file_name = localizer.simulation_path(simulation_input.run_dir, "run.out")
    os.makedirs(os.path.dirname(output_file_name), exist_ok=True)
    with open(output_file_name, "w") as file:
        file.write(terminal_output)


def _link_initial_particle_distribution(
    simulation_input: SimulationInput, localizer: HostLocalizer
):
    os.symlink(
        simulation_input.run_specs.Distribution,
        localizer.simulation_path(simulation_input.run_dir, "run.0000.001"),
    )


def _run_command(
    simulation_input: SimulationInput, localizer: HostLocalizer
) -> list[str]:
    cmd = [_astra_binary(simulation_input, localizer), "run.in"]

    if simulation_input.run_specs.thread_num > 1:
        cmd = ["mpirun", "-n", str(simulation_input.run_specs.thread_num)] + cmd
    return cmd


def _astra_binary(simulation_input: SimulationInput, localizer: HostLocalizer) -> str:
    binary = "astra"
    if simulation_input.run_specs.thread_num > 1:
        binary = "parallel_" + binary

    return localizer.astra_binary_path(binary)


def load_simulation_output(
    sim_id: str, localizer: HostLocalizer
) -> SimulationOutput | None:

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


def get_statistics(sim_id: str, localizer: HostLocalizer) -> StatisticsOutput:

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
