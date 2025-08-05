from abc import ABC, abstractmethod
import os
from astra_web.generator.schemas.io import GeneratorInput
from astra_web.simulation.schemas.io import SimulationInput
from .schemas.dispatch import DispatchResponse
from astra_web.file import write_txt


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

    def simulation_path(self, id: str, file_name: str | None = None) -> str:
        """
        Returns the path to the simulation file for the given ID.

        note: If no file_name is provided, the path to the simulation directory is returned.
            Otherwise, the path to the specific file is returned.
        """
        path = os.path.join(self.data_path(), "simulation", id)
        return path if file_name is None else os.path.join(path, file_name)

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
            name=f"generate-{generator_input.gen_id}",
            command=self._generator_command(generator_input),
            cwd=self.generator_path(generator_input.gen_id),
            output_file_name_base="generator",
        )

    def dispatch_simulation(
        self, simulation_input: SimulationInput
    ) -> DispatchResponse:
        """
        Dispatches a simulation to the host system.
        """
        return self._dispatch_command(
            name=f"simulate-{simulation_input.sim_id}",
            command=self._simulation_command(simulation_input),
            cwd=self.simulation_path(simulation_input.run_dir),
            output_file_name_base="run",
            timeout=simulation_input.run_specs.timeout,
            confirm_finished_successfully=True,
        )

    @abstractmethod
    def _dispatch_command(
        self,
        name: str,
        command: list[str],
        cwd: str,
        output_file_name_base: str,
        timeout: int | None = None,
        confirm_finished_successfully=False,
    ) -> DispatchResponse:
        """
        Dispatches a command with the specified directory and output configuration.

        :param command: The command to be executed on the host.
        :param cwd: The working directory where the command should be executed.
        :param output_file_name_base: The base name for the output files to be written to the working directory. (will be extended by .out and .err)
        :param timeout: Optional timeout for the command execution.
        :param confirm_finished_successfully: If True, will write a file named `FINISHED` in the working directory in case the command finished successfully.

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
