from abc import ABC, abstractmethod
import os
from astra_web.generator.schemas.io import GeneratorInput
from astra_web.simulation.schemas.io import SimulationInput
from .schemas.dispatch import DispatchResponse


class HostLocalizer(ABC):

    def __init__(self, *, do_not_init_manually_use_instance: None):
        pass

    GENERATE_DISPATCH_NAME_PREFIX = "generate-"
    SIMULATE_DISPATCH_NAME_PREFIX = "simulate-"

    @classmethod
    @abstractmethod
    def instance(cls) -> "HostLocalizer":
        """
        Returns the singleton instance of the host localizer.
        """
        pass

    @abstractmethod
    def data_path(self) -> str:
        """
        Returns the path to the data directory.
        """
        pass

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

    @abstractmethod
    def astra_binary_path(self, binary: str) -> str:
        """
        Returns the path to the Astra binary.
        """
        pass

    def dispatch_generation(
        self,
        generator_input: GeneratorInput,
        timeout: int,
    ) -> DispatchResponse:
        """
        Dispatches the generation process by running the ASTRA generator binary with the appropriate input file.
        """
        return self._dispatch_command(
            name=f"{self.GENERATE_DISPATCH_NAME_PREFIX}{generator_input.id}",
            command=self._generator_command(generator_input),
            cwd=self.generator_path(generator_input.id),
            output_file_name_base="generator",
            timeout=timeout,
        )

    def dispatch_simulation(
        self, simulation_input: SimulationInput
    ) -> DispatchResponse:
        """
        Dispatches a simulation to the host system.
        """
        return self._dispatch_command(
            name=f"{self.SIMULATE_DISPATCH_NAME_PREFIX}{simulation_input.id}",
            command=self._simulation_command(simulation_input),
            cwd=self.simulation_path(simulation_input.run_dir),
            output_file_name_base="run",
            timeout=simulation_input.run_specs.timeout,
        )

    @abstractmethod
    def _dispatch_command(
        self,
        name: str,
        command: list[str],
        cwd: str,
        output_file_name_base: str,
        timeout: int | None = None,
    ) -> DispatchResponse:
        """
        Dispatches a command with the specified directory and output configuration.

        :param command: The command to be executed on the host.
        :param cwd: The working directory where the command should be executed.
        :param output_file_name_base: The base name for the output files to be written to the working directory. (will be extended by .out and .err)
        :param timeout: Optional timeout for the command execution.

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

        if simulation_input.run_specs.thread_num > 1:
            cmd = ["mpirun", "-n", str(simulation_input.run_specs.thread_num)] + cmd
        return cmd

    def _astra_simulation_binary_path(
        self,
        simulation_input: SimulationInput,
    ) -> str:
        binary = "astra"
        if simulation_input.run_specs.thread_num > 1:
            binary = "parallel_" + binary

        return self.astra_binary_path(binary)
