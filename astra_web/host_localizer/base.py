from abc import ABC, abstractmethod
import os
from astra_web.generator.schemas.io import GeneratorInput
from astra_web.simulation.schemas.io import SimulationInput


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

    @abstractmethod
    def dispatch_generation(
        self,
        generator_input: GeneratorInput,
    ) -> None:
        """
        Dispatches the generation process by running the ASTRA generator binary with the appropriate input file.
        """
        pass

    @abstractmethod
    def dispatch_simulation(
        self,
        simulation_input: SimulationInput,
    ) -> None:
        """
        Dispatches a simulation to the host system.
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
