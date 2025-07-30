import os
from subprocess import run

from astra_web.generator.schemas.io import GeneratorInput
from astra_web.simulation.schemas.io import SimulationInput
from .base import HostLocalizer, write_to_file


class LocalHostLocalizer(HostLocalizer):

    _ASTRA_BINARY_PATH = os.environ["ASTRA_BINARY_PATH"]

    _DATA_PATH = "/app/data"
    _GENERATOR_DATA_PATH = os.path.join(_DATA_PATH, "generator")
    _SIMULATION_DATA_PATH = os.path.join(_DATA_PATH, "simulation")

    _instance = None

    @classmethod
    def instance(cls) -> "LocalHostLocalizer":
        if cls._instance is None:
            cls._instance = LocalHostLocalizer(do_not_init_manually_use_instance=None)
        return cls._instance

    def generator_path(self, id: str | None = None, extention: str = "") -> str:
        """
        Returns the path to the generator file for the given id and extension.
        """
        if id is None:
            return self._GENERATOR_DATA_PATH
        return os.path.join(self._GENERATOR_DATA_PATH, f"{id}{extention}")

    def simulation_path(self, id: str, file_name: str | None = None) -> str:
        """
        Returns the path to the simulation output for a given ID.

        note: If no file_name is provided, the path to the simulation directory is returned.
            Otherwise, the path to the specific file is returned.
        """
        if file_name is not None:
            return os.path.join(self._SIMULATION_DATA_PATH, id, file_name)
        return os.path.join(self._SIMULATION_DATA_PATH, id)

    def astra_binary_path(self, binary: str) -> str:
        """
        Returns the path to the Astra binary.
        """
        return os.path.join(self._ASTRA_BINARY_PATH, binary)

    def dispatch_generation(self, generator_input: GeneratorInput) -> None:
        self._dispatch_command(
            self._generator_command(generator_input),
            cwd=self.generator_path(),
            output_file_name_base=generator_input.gen_id,
        )

    def dispatch_simulation(self, simulation_input: SimulationInput) -> None:
        self._dispatch_command(
            self._simulation_command(simulation_input),
            cwd=self.simulation_path(simulation_input.run_dir),
            output_file_name_base="run",
            timeout=simulation_input.run_specs.timeout,
        )

    def _dispatch_command(
        self,
        command: list[str],
        cwd: str,
        output_file_name_base: str,
        timeout: int | None = None,
    ) -> None:
        """
        Runs a command in the specified directory and captures the output.
        """
        process = run(
            command,
            cwd=cwd,
            capture_output=True,
            timeout=timeout,
        )

        # write captured output to file
        stdout = process.stdout.decode()
        stdout_path = os.path.join(cwd, output_file_name_base + ".out")
        write_to_file(stdout, stdout_path)
        stderr = process.stderr.decode()
        stderr_path = os.path.join(cwd, output_file_name_base + ".err")
        write_to_file(stderr, stderr_path)
