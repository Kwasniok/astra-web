import os
from subprocess import run
from .base import HostLocalizer
from .schemas.dispatch import DispatchResponse
from astra_web.file import write_txt


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

    def data_path(self) -> str:
        return self._DATA_PATH

    def astra_binary_path(self, binary: str) -> str:
        """
        Returns the path to the Astra binary.
        """
        return os.path.join(self._ASTRA_BINARY_PATH, binary)

    def _dispatch_command(
        self,
        command: list[str],
        cwd: str,
        output_file_name_base: str,
        timeout: int | None = None,
        confirm_finished_successfully=False,
    ) -> DispatchResponse:
        """
        Runs a command in the specified directory and captures the output.
        """

        try:
            os.remove(os.path.join(cwd, "FINISHED"))
        except FileNotFoundError:
            pass

        os.makedirs(cwd, exist_ok=True)

        process = run(
            command,
            cwd=cwd,
            capture_output=True,
            timeout=timeout,
        )

        # write stdout/stderr
        stdout = process.stdout.decode()
        if stdout:
            stdout_path = os.path.join(cwd, output_file_name_base + ".out")
            write_txt(stdout, stdout_path)
        stderr = process.stderr.decode()
        if stderr:
            stderr_path = os.path.join(cwd, output_file_name_base + ".err")
            write_txt(stderr, stderr_path)

        if process.returncode == 0 and confirm_finished_successfully:
            success_path = os.path.join(cwd, "FINISHED")
            write_txt("", success_path)

        return DispatchResponse(dispatch_type="local")
