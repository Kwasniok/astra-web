import glob
import os
import re
from datetime import datetime
from shutil import rmtree
from typing import Any, Type, TypeVar
import numpy as np

from astra_web.dtypes import FloatPrecision
from astra_web._aux import filter_has_prefix, get_filter_subtree
from astra_web.file import read_json, read_txt, write_json, write_txt
from astra_web.generator.schemas.particles import Particles, ParticleCounts
from astra_web.host_localizer import HostLocalizer
from astra_web.simulation.schemas.auto_phase import CavityAutoPhaseTable
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
    local_localizer: HostLocalizer,
    host_localizer: HostLocalizer,
) -> SimulationDispatchOutput:
    """Dispatches the simulation run based on the provided simulation input.
    The simulation input is written to disk, and the run is dispatched to the appropriate host.
    """
    # local
    write_simulation_files(simulation_input, local_localizer)
    # 'remote'
    response = await host_localizer.dispatch_simulation(simulation_input)
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
        simulation_input.run.generator_id, "distribution.ini"
    )
    target = os.path.relpath(
        target, localizer.simulation_path(simulation_input.run_dir)
    )
    os.symlink(
        target,
        localizer.simulation_path(
            simulation_input.run_dir, simulation_input.run.distribution_file_name
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


class CompressionError(ValueError):
    """Raised when compression fails e.g. due to exceeding maximum relative error."""

    pass


def compress_simulation(
    sim_id: str,
    localizer: HostLocalizer,
    precision: FloatPrecision = FloatPrecision.FLOAT64,
    max_rel_err: float = 1e-4,
) -> None:
    """
    Compresses some simulation output files to save disk space.

    **WARNING**: **Deletes original files**.

    **WARNING**: Compression may be **lossy**, and is intended for reducing disk usage.

    **INFO**: Compression is **not idempotent**. Uncompress first before compressing again.

    - Compressed files:
        - Particle distribution files `run.0000.001` ... `run.<N>.001` -> `run.0000-<N>.001.f<P>.compressed.npz`

    Raises:
        ValueError: If the simulation with the given ID does not exist.
        FileExistsError: If the simulation is already compressed.
        CompressionError: If the maximum of the element-wise relative error exceeds `max_rel_error`.
    """
    if not os.path.exists(localizer.simulation_path(sim_id)):
        raise ValueError(f"Simulation with ID {sim_id} not found.")

    if glob.glob(
        localizer.simulation_path(sim_id, "run.*[0-9]-*[0-9].001.f*.compressed.npz")
    ):
        raise FileExistsError(
            f"Simulation with ID {sim_id} is already compressed. Uncompress first."
        )

    paths = _particle_paths(sim_id, localizer)
    keys = [k for k in map(lambda p: p.split(".")[-2], paths)]
    data: dict[str, np.typing.NDArray] = {
        k: _np_loadtxt_with_precision(p, precision, max_rel_err)
        for k, p in zip(keys, paths)
    }

    if len(data) > 0:
        compressed_path = localizer.simulation_path(
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
    localizer: HostLocalizer,
    high_precision: bool = True,
) -> None:
    """
    Uncompresses previously compressed simulation output files if available.

    - Uncompressed files:
        - Particle distribution files `run.0000-<N>.f<P>.compressed.npz` -> `run.0000.001` ... `run.<N>.001`

    - Note: Uncompression is an **idempotent** operation.

    Args:
        high_precision (bool): If `True`, writes floating point numbers with high precision (12 digits after the decimal point).  If `False`, uses 4 digits after the decimal point. See ASTRA documentation for details.

    Raises:
        ValueError: If the simulation with the given ID does not exist.
    """
    if not os.path.exists(localizer.simulation_path(sim_id)):
        raise ValueError(f"Simulation with ID {sim_id} not found.")

    try:
        compressed_path = _compressed_particle_path(sim_id, localizer)
        if compressed_path is None:
            return

        data = np.load(compressed_path)

        for k in data.keys():
            particle_path = localizer.simulation_path(sim_id, f"run.{k}.001")
            float_fmt = "%20.12E" if high_precision else "%20.4E"
            int_fmt = "%4d"
            np.savetxt(particle_path, data[k], fmt=[float_fmt] * 8 + [int_fmt] * 2)

        os.remove(compressed_path)
    except ValueError as e:
        raise RuntimeError(f"Failed to uncompress simulation with ID {sim_id}.") from e


def load_simulation_data(
    sim_id: str,
    localizer: HostLocalizer,
    include: list[str] | None = None,
) -> SimulationDataWithMeta | None:
    """
    Loads the entire simulation data for a given simulation ID.
    Returns None if the simulation does not exist.

    Parameters:
        include: Optional list of feature paths to include. All others are excluded. If `None`, all features are included.
            Example: `["input.run", "output"]`
    """

    if not os.path.exists(localizer.simulation_path(sim_id)):
        return None

    input = (
        read_json(SimulationInput, localizer.simulation_path(sim_id, "input.json"))
        if filter_has_prefix(include, "input")
        else None
    )

    output = (
        _load_output(sim_id, localizer, get_filter_subtree(include, "output"))
        if filter_has_prefix(include, "output")
        else None
    )

    astra_input = (
        read_txt(localizer.simulation_path(sim_id, "run.in"))
        if filter_has_prefix(include, "astra_input")
        else None
    )

    astra_output, meta = (
        _load_astra_output_and_meta(sim_id, localizer)
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
    localizer: HostLocalizer,
    include: list[str] | None = None,
) -> SimulationOutput:

    particles, final_particle_counts = (
        _load_particle_data(sim_id, localizer, include)
        if filter_has_prefix(include, "particles")
        or filter_has_prefix(include, "final_particle_counts")
        else (None, None)
    )

    norm_emittance_x, norm_emittance_y, norm_emittance_z = (
        _load_normalized_emittance(sim_id, localizer)
        if (
            filter_has_prefix(include, "norm_emittance_table_x")
            or filter_has_prefix(include, "norm_emittance_table_y")
            or filter_has_prefix(include, "norm_emittance_table_z")
        )
        else (None, None, None)
    )

    tr_sp_emittance = (
        _load_trace_space_emittance(sim_id, localizer)
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


def _load_particle_data(
    sim_id, localizer, include
) -> tuple[list[Particles], ParticleCounts]:

    final_only = include is not None and not filter_has_prefix(include, "particles")
    compressed_path = _compressed_particle_path(sim_id, localizer)
    if compressed_path is None:
        particles = _load_particle_data_from_raw_files(sim_id, localizer, final_only)
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


def _compressed_particle_path(sim_id: str, localizer: HostLocalizer) -> str | None:
    paths = glob.glob(
        localizer.simulation_path(sim_id, "run.*[0-9]-*[0-9].001.f*.compressed.npz")
    )
    if len(paths) > 1:
        raise RuntimeError(
            f"Multiple compressed particle files found for simulation with ID {sim_id}."
        )
    return paths[0] if len(paths) == 1 else None


def _particle_paths(id: str, localizer: HostLocalizer) -> list[str]:
    files = glob.glob(localizer.simulation_path(id, "run.*[0-9].001"))
    return sorted(
        files,
        key=lambda s: s.split(".")[1],
    )


def _load_particle_data_from_raw_files(
    sim_id: str, localizer: HostLocalizer, final_only: bool = False
) -> list[Particles]:

    particle_paths = _particle_paths(sim_id, localizer)

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


def get_generator_id(sim_id: str, localizer: HostLocalizer) -> str:
    if not os.path.exists(localizer.simulation_path(sim_id)):
        raise ValueError(f"Simulation with ID {sim_id} not found.")

    try:
        input = read_json(
            SimulationInput, localizer.simulation_path(sim_id, "input.json")
        )
        return input.run.generator_id
    except FileNotFoundError:
        raise ValueError(f"Input for simulation with ID {sim_id} not found.")


def _load_normalized_emittance(sim_id: str, localizer: HostLocalizer) -> tuple[
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
        path = localizer.simulation_path(sim_id, f"run.{coordinate.upper()}emit.001")
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
    sim_id: str, localizer: HostLocalizer
) -> TraceSpaceEmittanceTable | None:
    path = localizer.simulation_path(sim_id, "run.TREmit.001")
    try:
        return TraceSpaceEmittanceTable.read_from_csv(path)
    except FileNotFoundError:
        return None


def _load_astra_output_and_meta(
    sim_id: str, localizer: HostLocalizer
) -> tuple[str | None, SimulationMetaData]:

    status = get_simulation_status(sim_id, localizer)

    if not status == DispatchStatus.FINISHED:
        return None, SimulationMetaData(status=DispatchStatus.UNFINISHED)

    run_output = read_txt(localizer.simulation_path(sim_id, "run.out"))
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
            row = re.search(r"(\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)", line)
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
    localizer: HostLocalizer,
    state: DispatchStatus | None = None,
) -> list[str]:
    """
    Lists IDs of simulations.
    """
    ids_all = map(
        lambda p: os.path.split(p)[-1],
        glob.glob(localizer.simulation_path("*")),
    )

    if state is None:
        return sorted(ids_all)
    else:
        return sorted(
            id for id in ids_all if get_simulation_status(id, localizer) == state
        )


def list_simulation_states(
    localizer: HostLocalizer,
    sim_ids: list[str] | None = None,
) -> list[tuple[str, DispatchStatus]]:
    """
    Returns the current state of the simulations.
    """
    if sim_ids is None:
        sim_ids = list_simulation_ids(localizer)
    return list(
        (sim_id, get_simulation_status(sim_id, localizer)) for sim_id in sim_ids
    )


def delete_simulation(
    sim_id: str,
    localizer: HostLocalizer,
    force: bool = False,
) -> None:
    """
    Deletes the simulation directory for a given simulation ID.
    """
    path = localizer.simulation_path(sim_id)
    if os.path.exists(path):
        rmtree(path)


def get_simulation_status(sim_id: str, localizer: HostLocalizer) -> DispatchStatus:
    """
    Returns status of the simulation.
    """
    path = localizer.simulation_path(sim_id, "run.err")
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        return DispatchStatus.FAILED
    path = localizer.simulation_path(sim_id, "run.out")
    if os.path.isfile(path):
        run_out = read_txt(path)
        if "finished simulation" in run_out:
            return DispatchStatus.FINISHED
        if "Error" in run_out:
            return DispatchStatus.FAILED
    return DispatchStatus.UNFINISHED


def get_simulation_input_comment(sim_id: str, localizer: HostLocalizer) -> str | None:
    """
    Returns the comment of the simulation if available.
    """
    input = read_json(SimulationInput, localizer.simulation_path(sim_id, "input.json"))
    return input.comment
