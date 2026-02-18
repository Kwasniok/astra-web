import os
from subprocess import run

from .base import Actor, Task
from .schemas.any import DispatchResponse
from .schemas.config.local import LocalConfiguration


class LocalActor(Actor):

    def __init__(self, config: LocalConfiguration | None = None) -> None:
        super().__init__(config or LocalConfiguration())

    async def _dispatch_tasks(self, tasks: list[Task]) -> DispatchResponse:
        """
        Runs tasks in their respective directories and captures their output.
        """
        for task in tasks:
            await self._dispatch_task(task)
        return DispatchResponse(dispatch_type="local")

    async def _dispatch_task(self, task: Task) -> None:
        """
        Runs a single task in its respective directory and captures its output.
        """

        os.makedirs(task.cwd, exist_ok=True)

        stdout_path = os.path.join(task.cwd, task.output_file_name_base + ".out")
        stderr_path = os.path.join(task.cwd, task.output_file_name_base + ".err")

        with (
            open(stdout_path, "w") as stdout_file,
            open(stderr_path, "w") as stderr_file,
        ):
            run(
                task.command,
                cwd=task.cwd,
                stdout=stdout_file,
                stderr=stderr_file,
                timeout=task.timeout,
            )
