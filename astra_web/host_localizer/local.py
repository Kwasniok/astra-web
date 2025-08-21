import os
from subprocess import run
import threading
from .base import HostLocalizer
from .schemas.dispatch import DispatchResponse
from astra_web.file import write_txt


class LocalHostLocalizer(HostLocalizer):

    _ASTRA_BINARY_PATH = os.environ["ASTRA_BINARY_PATH"]
    _DATA_PATH = os.environ["ASTRA_DATA_PATH"]

    _instance = None

    _dispatched_threads: list[threading.Thread] = []

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
        name: str,
        command: list[str],
        cwd: str,
        output_file_name_base: str,
        timeout: int | None = None,
    ) -> DispatchResponse:
        """
        Runs a command in the specified directory and captures the output.
        """

        os.makedirs(cwd, exist_ok=True)

        kwargs = dict(
            command=command,
            cwd=cwd,
            output_file_name_base=output_file_name_base,
            timeout=timeout,
            env=os.environ,
        )
        thread = threading.Thread(target=_dispatch_command, kwargs=kwargs, name=name)
        thread.start()

        self._dispatched_threads.append(thread)

        return DispatchResponse(dispatch_type="local")

    def join_all_dispatched_threads(self):
        """
        Join all dispatched threads and forget them.
        """
        for thread in self._dispatched_threads:
            thread.join()
        self._dispatched_threads.clear()


def _dispatch_command(
    command: list[str],
    cwd: str,
    output_file_name_base: str,
    timeout: int | None = None,
    env: dict[str, str] | None = None,
):
    """
    internal only: Command dispatch as global function for threading.Thread.
    """

    process = run(
        command,
        cwd=cwd,
        capture_output=True,
        timeout=timeout,
        env=env,
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
