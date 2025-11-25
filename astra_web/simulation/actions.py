import glob
import os
import re
from datetime import datetime
from shutil import rmtree
from typing import Type, TypeVar
import numpy as np

from astra_web.dtypes import FloatPrecision
from astra_web.features.schemas.io import FeatureConfig
from astra_web.filter import filter_has_prefix, get_filter_subtree
from astra_web.file import read_json, read_txt, write_json, write_txt
from astra_web.generator.schemas.particles import Particles, ParticleCounts
from astra_web.actor import Actor
from astra_web.simulation.schemas.auto_phase import CavityAutoPhaseTable
from astra_web.simulation.schemas.compression import CompressionReport
from astra_web.status import DispatchStatus

from .schemas.emittance_table import (
    LongitudinalNormalizedEmittanceTable,
    TraceSpaceEmittanceTable,
    Transversal1DNormalizedEmittanceTable,
)
from .schemas.io import (
    SimulationDataWithMeta,
    SimulationDispatchOutput,
    SimulationInput,
    SimulationMetaData,
    SimulationOutput,
)


async def dispatch_simulation_run(
    simulation_input: SimulationInput,
    local_actor: Actor,
    host_actor: Actor,
) -> SimulationDispatchOutput:
    """Dispatches the simulation run based on the provided simulation input.
    The simulation input is written to disk, and the run is dispatched to the appropriate host.
    """
    # local
    write_simulation_files(simulation_input, local_actor)
    # 'remote'
    response = await host_actor.dispatch_simulation(simulation_input)
    return SimulationDispatchOutput(
        sim_id=simulation_input.run_dir,
        dispatch_response=response,
    )


async def redispatch_simulation_run(
    sim_id: str,
    actor: Actor,
) -> SimulationDispatchOutput:
    """
    Redispatches the simulation run based on an existing simulation ID.

    The existing simulation input is loaded from disk, and the run is dispatched to the appropriate host.
    """

    _reset_simulation(sim_id, actor)

    simulation_input = load_simulation_input(sim_id, actor)
    if simulation_input is None:
        raise FileNotFoundError(f"Simulation input for ID {sim_id} not found.")

    response = await actor.dispatch_simulation(simulation_input)
    return SimulationDispatchOutput(
        sim_id=sim_id,
        dispatch_response=response,
    )


def write_simulation_files(simulation_input: SimulationInput, actor: Actor) -> None:
    """
    Write the simulation input to disk, including the INI file, element files, input JSON and linking the initial parSimulationDataticle distribution.
    """
    run_path = actor.simulation_path(simulation_input.run_dir)
    os.makedirs(run_path, exist_ok=True)
    write_json(
        simulation_input,
        actor.simulation_path(simulation_input.run_dir, "input.json"),
    )
    write_txt(
        simulation_input.to_ini(),
        actor.simulation_path(simulation_input.run_dir, "run.in"),
    )
    _link_initial_particle_distribution(simulation_input, actor)
    _link_field_files(simulation_input, actor)


def _link_initial_particle_distribution(
    simulation_input: SimulationInput, actor: Actor
):
    # make link relative to ensure compatibility across hosts
    target = actor.generator_path(simulation_input.run.generator_id, "distribution.ini")
    target = os.path.relpath(target, actor.simulation_path(simulation_input.run_dir))
    os.symlink(
        target,
        actor.simulation_path(
            simulation_input.run_dir, simulation_input.run.distribution_file_name
        ),
    )


def _link_field_files(simulation_input: SimulationInput, actor: Actor):
    for file_name in simulation_input.field_file_names:
        _link_field_file(file_name, simulation_input.run_dir, actor)


def _link_field_file(file_name: str, run_dir: str, actor: Actor):
    # make link relative to ensure compatibility across hosts
    target = actor.field_path(file_name)
    target = os.path.relpath(target, actor.simulation_path(run_dir))
    os.symlink(target, actor.simulation_path(run_dir, file_name))


def _reset_simulation(
    sim_id: str,
    actor: Actor,
) -> None:
    """
    Clears ALL simulation files and rewrites the initially required files.

    Raises:
        FileNotFoundError: If no simulation input for the given ID is found.
    """
    input = load_simulation_input(sim_id, actor)
    if input is None:
        raise FileNotFoundError(
            f"No simulation input for ID {sim_id} found. Cannot reset safely."
        )
    delete_simulation(sim_id, actor)
    write_simulation_files(input, actor)


class CompressionError(ValueError):
    """Raised when compression fails e.g. due to exceeding maximum relative error."""

    pass


def compress_simulation(
    sim_id: str,
    actor: Actor,
    precision: FloatPrecision = FloatPrecision.FLOAT64,
    max_rel_err: float = 1e-4,
) -> CompressionReport | None:
    """
    Compresses some simulation output files to save disk space.

    **WARNING**: **Deletes original files**.

    **WARNING**: Compression may be **lossy**, and is intended for reducing disk usage.

    **INFO**: Compression is **not idempotent**. Uncompress first before compressing again.

    - Compressed files:
        - Particle distribution files `run.<M>.001` ... `run.<N>.001` -> `run.<M>-<N>.001.f<P>.compressed.npz`

    Returns:
        - `CompressionReport` summarizing the compression operation.
        - `None` if there is nothing to be compressed.

    Raises:
        ValueError: If the simulation with the given ID does not exist.
        FileExistsError: If the simulation is already compressed.
        CompressionError: Compression not possible - e.g. if the simulation has not finished yet or if the maximum of the element-wise relative error exceeds `max_rel_error`.
    """

    if not os.path.exists(actor.simulation_path(sim_id)):
        raise ValueError(f"Simulation with ID {sim_id} not found.")

    if get_simulation_status(sim_id, actor) != DispatchStatus.FINISHED:
        raise CompressionError(f"Simulation with ID {sim_id} is not finished.")

    if glob.glob(
        actor.simulation_path(sim_id, "run.*[0-9]-*[0-9].001.f*.compressed.npz")
    ):
        raise FileExistsError(
            f"Simulation with ID {sim_id} is already compressed. Uncompress first."
        )

    paths = _particle_paths(sim_id, actor)

    total_original_size = sum(os.path.getsize(p) for p in paths)

    keys = [k for k in map(lambda p: p.split(".")[-2], paths)]
    data: dict[str, np.typing.NDArray] = {
        k: _np_loadtxt_with_precision(p, precision, max_rel_err)
        for k, p in zip(keys, paths)
    }

    if len(data) > 0:
        compressed_path = actor.simulation_path(
            sim_id,
            f"run.{keys[0]}-{keys[-1]}.001.{precision.value}.compressed.npz",
        )
        np.savez_compressed(
            compressed_path,
            **data,
            allow_pickle=False,
        )
        if os.path.exists(compressed_path):
            for p in paths:
                os.remove(p)

        total_new_size = os.path.getsize(compressed_path)

        return CompressionReport(
            original_files=[os.path.basename(p) for p in paths],
            new_files=[os.path.basename(compressed_path)],
            total_original_size=total_original_size,
            total_new_size=total_new_size,
            compression_ratio=(total_original_size / total_new_size),
        )

    return None


def _np_loadtxt_with_precision(
    path: str,
    precision: FloatPrecision,
    max_rel_err: float,
) -> np.typing.NDArray:
    """
    Loads a text file with numpy and converts it to the specified precision.

    Raises:
        CompressionError: If the maximum of the element-wise relative error exceeds `max_rel_error`.
    """
    data = np.loadtxt(path)
    data_compressed = data.astype(precision.numpy_dtype())

    rel_error = lambda x, y: np.max(np.abs(x - y) / np.maximum(np.abs(x), 1e-12))
    if rel_error(data, data_compressed) > max_rel_err:
        raise CompressionError(
            f"Compression of particle data in file {path} exceeds maximum relative error of {max_rel_err}."
        )

    return data_compressed


def uncompress_simulation(
    sim_id: str,
    actor: Actor,
    high_precision: bool = True,
) -> CompressionReport | None:
    """
    Uncompresses previously compressed simulation output files if available.

    - Uncompressed files:
        - Particle distribution files `run.<M>-<N>.f<P>.compressed.npz` -> `run.<M>.001` ... `run.<N>.001`

    - Note: Uncompression is an **idempotent** operation.

    Args:
        high_precision (bool): If `True`, writes floating point numbers with high precision (12 digits after the decimal point).  If `False`, uses 4 digits after the decimal point. See ASTRA documentation for details.

    Returns:
        - `CompressionReport` summarizing the uncompression operation.
        - `None` if the simulation is already uncompressed.

    Raises:
        ValueError: If the simulation with the given ID does not exist.
        FileNotFoundError: If multiple compressed particle files are found.
        CompressionError: If uncompression fails.
    """
    if not os.path.exists(actor.simulation_path(sim_id)):
        raise ValueError(f"Simulation with ID {sim_id} not found.")

    compressed_path = _compressed_particle_path(sim_id, actor)
    if compressed_path is None:
        # already uncompressed
        return None

    total_original_size = os.path.getsize(compressed_path)

    try:
        data = np.load(compressed_path)

        for k in data.keys():
            particle_path = actor.simulation_path(sim_id, f"run.{k}.001")
            float_fmt = "%20.12E" if high_precision else "%20.4E"
            int_fmt = "%4d"
            np.savetxt(particle_path, data[k], fmt=[float_fmt] * 8 + [int_fmt] * 2)
    except ValueError as e:
        raise CompressionError(
            f"Failed to uncompress simulation with ID {sim_id}."
        ) from e

    os.remove(compressed_path)

    total_new_size = sum(
        os.path.getsize(actor.simulation_path(sim_id, f"run.{k}.001"))
        for k in data.keys()
    )

    return CompressionReport(
        original_files=[os.path.basename(compressed_path)],
        new_files=[f"run.{k}.001" for k in data.keys()],
        total_original_size=total_original_size,
        total_new_size=total_new_size,
        compression_ratio=(total_original_size / total_new_size),
    )


def is_compressed_simulation(
    sim_id: str,
    actor: Actor,
) -> bool:
    """
    Checks if the simulation with the given ID is compressed.

    Raises:
        ValueError: If the simulation with the given ID does not exist.
        FileNotFoundError: If multiple compressed particle files are found.
    """
    if not os.path.exists(actor.simulation_path(sim_id)):
        raise ValueError(f"Simulation with ID {sim_id} not found.")

    compressed_path = _compressed_particle_path(sim_id, actor)
    return compressed_path is not None


def load_simulation_data(
    sim_id: str,
    actor: Actor,
    include: list[str] | None = None,
    config: FeatureConfig = FeatureConfig(),
) -> SimulationDataWithMeta | None:
    """
    Loads the entire simulation data for a given simulation ID.
    Returns None if the simulation does not exist.

    Parameters:
        include: Optional list of feature paths to include. All others are excluded. If `None`, all features are included.
            Example: `["input.run", "output"]`
    """

    if not os.path.exists(actor.simulation_path(sim_id)):
        return None

    input = (
        load_simulation_input(sim_id, actor)
        if filter_has_prefix(include, "input")
        else None
    )

    output = (
        _load_output(sim_id, actor, get_filter_subtree(include, "output"))
        if filter_has_prefix(include, "output")
        else None
    )

    astra_input = (
        read_txt(actor.simulation_path(sim_id, "run.in"))
        if filter_has_prefix(include, "astra_input")
        else None
    )

    astra_output, meta = (
        _load_astra_output_and_meta(sim_id, actor)
        if filter_has_prefix(include, "astra_output")
        or filter_has_prefix(include, "meta")
        else (None, None)
    )

    return SimulationDataWithMeta(
        input=input,
        output=output,
        input_astra=astra_input,
        output_astra=astra_output,
        meta=meta,
    )


def _load_output(
    sim_id: str,
    actor: Actor,
    include: list[str] | None = None,
    config: FeatureConfig = FeatureConfig(),
) -> SimulationOutput:

    particles, final_particle_counts = (
        _load_particle_data(sim_id, actor, include)
        if filter_has_prefix(include, "particles")
        or filter_has_prefix(include, "final_particle_counts")
        else (None, None)
    )

    norm_emittance_x, norm_emittance_y, norm_emittance_z = (
        _load_normalized_emittance(sim_id, actor)
        if (
            filter_has_prefix(include, "norm_emittance_table_x")
            or filter_has_prefix(include, "norm_emittance_table_y")
            or filter_has_prefix(include, "norm_emittance_table_z")
        )
        else (None, None, None)
    )

    tr_sp_emittance = (
        _load_trace_space_emittance(sim_id, actor)
        if filter_has_prefix(include, "trace_space_emittance_table")
        else None
    )

    return SimulationOutput(
        particles=particles,
        final_particle_counts=final_particle_counts,
        norm_emittance_table_x=norm_emittance_x,
        norm_emittance_table_y=norm_emittance_y,
        norm_emittance_table_z=norm_emittance_z,
        trace_space_emittance_table=tr_sp_emittance,
    )


def load_simulation_input(sim_id: str, actor: Actor) -> SimulationInput | None:
    """
    Loads the simulation input for a given simulation ID.
    """
    path = actor.simulation_path(sim_id, "input.json")
    if os.path.exists(path):
        input = read_json(SimulationInput, path)
        input._id = sim_id
        return input
    return None


def _load_particle_data(
    sim_id: str, actor: Actor, include: list[str] | None
) -> tuple[list[Particles], ParticleCounts]:

    final_only = include is not None and not filter_has_prefix(include, "particles")
    compressed_path = _compressed_particle_path(sim_id, actor)
    if compressed_path is None:
        particles = _load_particle_data_from_raw_files(sim_id, actor, final_only)
    else:
        particles = _load_particle_data_from_compressed_file(
            compressed_path, final_only
        )

    final_particle_counts = ParticleCounts(
        total=len(particles[-1].x),
        active=int(sum(particles[-1].active_particles)),
        lost=int(sum(particles[-1].lost_particles)),
    )

    return particles, final_particle_counts


def _compressed_particle_path(sim_id: str, actor: Actor) -> str | None:
    """
    Returns the path to the compressed particle file if it exists.

    Raises:
        FileNotFoundError: If multiple compressed particle files are found.
    """
    paths = glob.glob(
        actor.simulation_path(sim_id, "run.*[0-9]-*[0-9].001.f*.compressed.npz")
    )
    if len(paths) > 1:
        raise FileNotFoundError(
            f"Multiple compressed particle files found for simulation with ID {sim_id}."
        )
    return paths[0] if len(paths) == 1 else None


def _particle_paths(id: str, actor: Actor) -> list[str]:
    files = glob.glob(actor.simulation_path(id, "run.*[0-9].001"))
    return sorted(
        files,
        key=lambda s: s.split(".")[1],
    )


def _load_particle_data_from_raw_files(
    sim_id: str, actor: Actor, final_only: bool = False
) -> list[Particles]:

    particle_paths = _particle_paths(sim_id, actor)

    if final_only:
        particle_paths = particle_paths[-1:]

    particles = [Particles.read_from_csv(path) for path in particle_paths]

    return particles


def _load_particle_data_from_compressed_file(
    compressed_path: str,
    final_only: bool = False,
) -> list[Particles]:
    data = np.load(compressed_path)

    particle_keys = sorted(data.keys())

    if final_only:
        particle_keys = particle_keys[-1:]

    particles = [Particles.from_array(data[k]) for k in particle_keys]

    return particles


def get_generator_id(sim_id: str, actor: Actor) -> str:
    if not os.path.exists(actor.simulation_path(sim_id)):
        raise ValueError(f"Simulation with ID {sim_id} not found.")

    try:
        input = read_json(SimulationInput, actor.simulation_path(sim_id, "input.json"))
        return input.run.generator_id
    except FileNotFoundError:
        raise ValueError(f"Input for simulation with ID {sim_id} not found.")


def _load_normalized_emittance(sim_id: str, actor: Actor) -> tuple[
    Transversal1DNormalizedEmittanceTable | None,
    Transversal1DNormalizedEmittanceTable | None,
    LongitudinalNormalizedEmittanceTable | None,
]:

    T = TypeVar(
        "T",
        bound=Transversal1DNormalizedEmittanceTable
        | LongitudinalNormalizedEmittanceTable,
    )

    def load(cls: Type[T], coordinate: str) -> T | None:
        path = actor.simulation_path(sim_id, f"run.{coordinate.upper()}emit.001")
        try:
            return cls.read_from_csv(path)
        except FileNotFoundError:
            return None

    return (
        load(Transversal1DNormalizedEmittanceTable, "x"),
        load(Transversal1DNormalizedEmittanceTable, "y"),
        load(LongitudinalNormalizedEmittanceTable, "z"),
    )


def _load_trace_space_emittance(
    sim_id: str, actor: Actor
) -> TraceSpaceEmittanceTable | None:
    path = actor.simulation_path(sim_id, "run.TREmit.001")
    try:
        return TraceSpaceEmittanceTable.read_from_csv(path)
    except FileNotFoundError:
        return None


def _load_astra_output_and_meta(
    sim_id: str, actor: Actor
) -> tuple[str | None, SimulationMetaData]:

    status = get_simulation_status(sim_id, actor)

    if not status == DispatchStatus.FINISHED:
        return None, SimulationMetaData(status=DispatchStatus.UNFINISHED)

    is_compressed = is_compressed_simulation(sim_id, actor)

    run_output = read_txt(actor.simulation_path(sim_id, "run.out"))
    finished_date = None
    execution_time = None
    warnings: list[str] = []
    cavity_auto_phase: CavityAutoPhaseTable | None = None
    # helper:
    section_auto_phase_line: int | None = None

    for n, line in enumerate(run_output.splitlines()):
        if "finished simulation" in line:
            date_match = re.search(
                r"(\d{1,2})\.\s*(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})", line
            )
            if date_match:
                day, month, year, hour, minute = map(int, date_match.groups())
                finished_date = datetime(year, month, day, hour, minute)
        elif "execution time" in line:
            hour_match = re.search(r"(\d+)\sh", line)
            minute_match = re.search(r"(\d+)\s*min", line)
            second_match = re.search(r"([\d.]+)\s*se[c|k]", line)
            hours = int(hour_match.group(1)) if hour_match else 0
            minutes = int(minute_match.group(1)) if minute_match else 0
            seconds = float(second_match.group(1)) if second_match else 0.0
            execution_time = hours * 3600 + minutes * 60 + seconds
        elif "ATTENTION" in line:
            attention_match = re.search(r"ATTENTION:\s*(.*)", line)
            if attention_match:
                warnings.append(attention_match.group(1))
        elif "WARNING" in line:
            warning_match = re.search(r"WARNING:\s*(.*)", line)
            if warning_match:
                warnings.append(warning_match.group(1))
        elif "Cavity phasing completed" in line:
            section_auto_phase_line = n
            # do the parsing later

    # deferred parsing:
    if section_auto_phase_line is not None:
        cavity_auto_phase = _read_auto_phase_table(run_output, section_auto_phase_line)

    return (
        run_output,
        SimulationMetaData(
            status=status,
            finished_date=finished_date,
            execution_time=execution_time,
            warnings=warnings,
            cavity_auto_phasing=cavity_auto_phase,
            is_compressed=is_compressed,
        ),
    )


def _read_auto_phase_table(run_output: str, start_line: int) -> CavityAutoPhaseTable:
    lines = run_output.splitlines()

    energy_gain: list[float] = []
    phase: list[float] = []
    for n, line in enumerate(lines[start_line + 1 :]):

        if n == 0:
            # verify table header and units
            header = re.search(
                r"Cavity number\s+Energy gain\s+\[MeV\]\s+at\s+Phase \[deg\]", line
            )
            if not header:
                raise RuntimeError(
                    f"Failed to parse cavity auto phase table: Invalid header line (`{line}`)."
                )
        else:
            row = re.search(r"(\d+)\s+(\d+\.\d*)\s+([+-]?\d+\.\d*)", line)
            end = re.search(r"^\s*(-)+\s*$", line)
            if row:
                num, eg, phi = row.groups()

                if num != str(n):
                    raise RuntimeError(
                        f"Failed to parse cavity auto phase table: Unexpected cavity number in line (`{line}`)."
                    )

                energy_gain.append(float(eg))
                phase.append(float(phi))
            elif end:
                break  # end of table
            else:
                # unexpected line
                raise RuntimeError(
                    f"Failed to parse cavity auto phase table: Unexpected line (`{line}`)."
                )

    return CavityAutoPhaseTable(
        energy_gain=energy_gain,
        absolute_phase=phase,
    )


def list_simulation_ids(
    actor: Actor,
    state: DispatchStatus | None = None,
) -> list[str]:
    """
    Lists IDs of simulations.
    """
    ids_all = map(
        lambda p: os.path.basename(p),
        glob.glob(actor.simulation_path("*")),
    )

    if state is None:
        return sorted(ids_all)
    else:
        return sorted(id for id in ids_all if get_simulation_status(id, actor) == state)


def list_simulation_states(
    actor: Actor,
    sim_ids: list[str] | None = None,
) -> list[tuple[str, DispatchStatus]]:
    """
    Returns the current state of the simulations.
    """
    if sim_ids is None:
        sim_ids = list_simulation_ids(actor)
    return list((sim_id, get_simulation_status(sim_id, actor)) for sim_id in sim_ids)


def delete_simulation(
    sim_id: str,
    actor: Actor,
    force: bool = False,
) -> None:
    """
    Deletes the simulation directory for a given simulation ID.
    """
    path = actor.simulation_path(sim_id)
    if os.path.exists(path):
        rmtree(path)


def get_simulation_status(sim_id: str, actor: Actor) -> DispatchStatus:
    """
    Returns status of the simulation.
    """
    path = actor.simulation_path(sim_id, "run.err")
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        return DispatchStatus.FAILED
    path = actor.simulation_path(sim_id, "run.out")
    if os.path.isfile(path):
        run_out = read_txt(path)
        if "Error" in run_out:
            return DispatchStatus.FAILED
        if "ATTENTION" in run_out:
            return DispatchStatus.FAILED
        if "finished simulation" in run_out:
            return DispatchStatus.FINISHED
    return DispatchStatus.UNFINISHED


def get_simulation_input_comment(sim_id: str, actor: Actor) -> str | None:
    """
    Returns the comment of the simulation if available.
    """
    input = read_json(SimulationInput, actor.simulation_path(sim_id, "input.json"))
    return input.comment
