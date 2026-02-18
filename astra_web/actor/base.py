from abc import ABC, abstractmethod
from dataclasses import dataclass
import os
from astra_web.generator.schemas.io import GeneratorInput
from astra_web.simulation.schemas.compression import CompressionConfig
from astra_web.simulation.schemas.io import SimulationInput
from .schemas.any import DispatchResponse
from .schemas.config import BaseConfiguration


@dataclass
class Task:
    name: str
    command: list[str]
    cwd: str
    output_file_name_base: str
    timeout: int | None = None
    threads: int | None = None


class Actor(ABC):
    """
    Abstract base class for data storage and processing management.

    Depending on which computer (host) is used for a task, different
    implementations of this class may be used to manage data paths and command
    dispatching.
    """

    def __init__(self, config: BaseConfiguration) -> None:
        self._config = config

    GENERATE_DISPATCH_NAME_PREFIX = "generate-"
    SIMULATE_DISPATCH_NAME_PREFIX = "simulate-"
    COMPRESS_DISPATCH_NAME_PREFIX = "compress-"

    def data_path(self) -> str:
        """
        Returns the path to the data directory.
        """
        return self._config._data_path

    def generator_path(self, id: str, file_name: str | None = None) -> str:
        """
        Returns the path to the generator file for the given ID.
        """
        path = os.path.join(self.data_path(), "generator", id)
        return path if file_name is None else os.path.join(path, file_name)

    def field_path(self, file_name: str | None = None) -> str:
        """
        Returns the path to the field file for the given ID.
        """
        path = os.path.join(self.data_path(), "field")
        return path if file_name is None else os.path.join(path, file_name)

    def simulation_path(self, id: str, file_name: str | None = None) -> str:
        """
        Returns the path to the simulation file for the given ID.

        note: If no file_name is provided, the path to the simulation directory is returned.
            Otherwise, the path to the specific file is returned.
        """
        path = os.path.join(self.data_path(), "simulation", id)
        return path if file_name is None else os.path.join(path, file_name)

    @property
    def generator_ids(self) -> list[str]:
        """
        Returns the list of all managed generator IDs.
        """
        path = os.path.join(self.data_path(), "generator")
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

    @property
    def simulation_ids(self) -> list[str]:
        """
        Returns the list of all managed simulation IDs.
        """
        path = os.path.join(self.data_path(), "simulation")
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

    def astra_binary_path(self, binary: str) -> str:
        """
        Returns the path to the Astra binary.
        """
        return os.path.join(self._config._astra_binary_path, binary)

    async def dispatch_generation(
        self, generator_input: GeneratorInput
    ) -> DispatchResponse:
        """
        Dispatches the generation process by running the ASTRA generator binary with the appropriate input file.
        """
        return await self._dispatch_tasks(
            [
                Task(
                    name=f"{self.GENERATE_DISPATCH_NAME_PREFIX}{generator_input.id}",
                    command=self._generator_command(generator_input),
                    cwd=self.generator_path(generator_input.id),
                    output_file_name_base="generator",
                    timeout=generator_input.timeout,
                )
            ]
        )

    async def dispatch_simulation(
        self, simulation_input: SimulationInput
    ) -> DispatchResponse:
        """
        Dispatches a simulation to the host system.
        """
        tasks = [
            Task(
                name=f"{self.SIMULATE_DISPATCH_NAME_PREFIX}{simulation_input.id}",
                command=self._simulation_command(simulation_input),
                cwd=self.simulation_path(simulation_input.run_dir),
                output_file_name_base="run",
                timeout=simulation_input.run.timeout,
                threads=simulation_input.run.thread_num,
            ),
        ]

        if simulation_input.auto_compress_after_run is not None:
            tasks.append(
                Task(
                    name=f"{self.COMPRESS_DISPATCH_NAME_PREFIX}{simulation_input.id}",
                    command=self._compression_command(
                        sim_id=simulation_input.id,
                        config=simulation_input.auto_compress_after_run,
                    ),
                    cwd=self.simulation_path(simulation_input.run_dir),
                    output_file_name_base="compress",
                )
            )

        return await self._dispatch_tasks(tasks)

    @abstractmethod
    async def _dispatch_tasks(self, tasks: list[Task]) -> DispatchResponse:
        """
        Dispatches a task with the specified directory and output configuration.

        May create additional files with the captured stdout (.out) and stderr (.err) inside of `cwd` when non-empty.
        """
        pass

    def _generator_command(self, generator_input: GeneratorInput) -> list[str]:
        return [
            self.astra_binary_path("generator"),
            f"generator.in",
        ]

    def _simulation_command(self, simulation_input: SimulationInput) -> list[str]:
        cmd = [self._astra_simulation_binary_path(simulation_input), "run.in"]

        if simulation_input.run.thread_num > 1:
            cmd = ["mpirun", "-n", str(simulation_input.run.thread_num)] + cmd
        return cmd

    def _compression_command(
        self,
        sim_id: str,
        config: CompressionConfig,
    ) -> list[str]:
        cmd = [
            self.astra_binary_path("astra-web-cli"),
            "compress-sim",
            f"--sim-id={sim_id}",
        ]
        cmd.append(f"--precision={config.precision.value}")
        cmd.append(f"--max-rel-err={config.max_rel_err}")
        return cmd

    def _astra_simulation_binary_path(
        self,
        simulation_input: SimulationInput,
    ) -> str:
        binary = "astra"
        if simulation_input.run.thread_num > 1:
            binary = "parallel_" + binary

        return self.astra_binary_path(binary)
