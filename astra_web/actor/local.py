import os
from subprocess import run
import threading
from .base import Actor
from .schemas.any import DispatchResponse


class LocalActor(Actor):

    _ASTRA_BINARY_PATH = os.environ["ASTRA_BINARY_PATH"]
    _DATA_PATH = os.environ["ASTRA_DATA_PATH"]

    _instance = None

    _dispatched_threads: list[threading.Thread] = []

    @classmethod
    def instance(cls) -> "LocalActor":
        if cls._instance is None:
            cls._instance = LocalActor(do_not_init_manually_use_instance=None)
        return cls._instance

    def data_path(self) -> str:
        return self._DATA_PATH

    def astra_binary_path(self, binary: str) -> str:
        """
        Returns the path to the Astra binary.
        """
        return os.path.join(self._ASTRA_BINARY_PATH, binary)

    async def _dispatch_command(
        self,
        name: str,
        command: list[str],
        cwd: str,
        output_file_name_base: str,
        timeout: int | None = None,
        threads: int | None = None,
    ) -> DispatchResponse:
        """
        Runs a command in the specified directory and captures the output.
        """

        os.makedirs(cwd, exist_ok=True)

        stdout_path = os.path.join(cwd, output_file_name_base + ".out")
        stderr_path = os.path.join(cwd, output_file_name_base + ".err")

        with open(stdout_path, "w") as stdout_file, open(
            stderr_path, "w"
        ) as stderr_file:
            run(
                command,
                cwd=cwd,
                stdout=stdout_file,
                stderr=stderr_file,
                timeout=timeout,
            )

        return DispatchResponse(dispatch_type="local")

    def join_all_dispatched_threads(self):
        """
        Join all dispatched threads and forget them.
        """
        for thread in self._dispatched_threads:
            thread.join()
        self._dispatched_threads.clear()
