from abc import ABC, abstractmethod
import os
from astra_web.generator.schemas.io import GeneratorInput
from astra_web.simulation.schemas.io import SimulationInput
from .schemas.dispatch import DispatchResponse


class HostLocalizer(ABC):

    def __init__(self, *, do_not_init_manually_use_instance: None):
        pass

    @classmethod
    @abstractmethod
    def instance(cls) -> "HostLocalizer":
        """
        Returns the singleton instance of the host localizer.
        """
        pass

    @abstractmethod
    def generator_path(self, id: str | None = None, extention: str = "") -> str:
        """
        Returns the path to the generator file for the given id and extension.
        """
        pass

    @abstractmethod
    def simulation_path(self, id: str, file_name: str | None = None) -> str:
        """
        Returns the path to the simulation output for a given ID.

        note: If no file_name is provided, the path to the simulation directory is returned.
            Otherwise, the path to the specific file is returned.
        """
        pass

    @abstractmethod
    def astra_binary_path(self, binary: str) -> str:
        """
        Returns the path to the Astra binary.
        """
        pass

    def dispatch_generation(self, generator_input: GeneratorInput) -> DispatchResponse:
        """
        Dispatches the generation process by running the ASTRA generator binary with the appropriate input file.
        """
        return self._dispatch_command(
            self._generator_command(generator_input),
            cwd=self.generator_path(),
            output_file_name_base=generator_input.gen_id,
        )

    def dispatch_simulation(
        self, simulation_input: SimulationInput
    ) -> DispatchResponse:
        """
        Dispatches a simulation to the host system.
        """
        return self._dispatch_command(
            self._simulation_command(simulation_input),
            cwd=self.simulation_path(simulation_input.run_dir),
            output_file_name_base="run",
            timeout=simulation_input.run_specs.timeout,
        )

    @abstractmethod
    def _dispatch_command(
        self,
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
        """
        pass

    def _generator_command(self, generator_input: GeneratorInput) -> list[str]:
        return [
            self.astra_binary_path("generator"),
            f"{generator_input.gen_id}.in",
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


def write_to_file(content: str, file_path: str) -> None:
    """
    Writes the content to a file.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as file:
        file.write(content)
