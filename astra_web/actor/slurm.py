from typing import Any, Callable
import os
import slurm_requests as slurm
from slurm_requests import RequestMethod, JSON
from .base import Actor, Task
from .schemas.any import DispatchResponse
from .schemas.config.slurm import SLURMConfiguration
from astra_web.uuid import get_uuid


class SLURMActor(Actor):

    def __init__(self, config: SLURMConfiguration) -> None:
        super().__init__(config)

    def data_path(self) -> str:
        """
        Returns the path to the data directory.
        """
        config: SLURMConfiguration = self._config
        return config.data_path or super().data_path()

    def astra_binary_path(self, binary: str) -> str:
        """
        Returns the path to the Astra binary.
        """
        config: SLURMConfiguration = self._config
        return (
            os.path.join(config.astra_binary_path, binary)
            if config.astra_binary_path is not None
            else super().astra_binary_path(binary)
        )

    @property
    def _header_credentials(self) -> dict[str, str]:
        """
        Returns the headers used for SLURM requests.
        """
        config: SLURMConfiguration = self._config
        return {
            "X-SLURM-USER-NAME": config.user_name,
            "X-SLURM-USER-TOKEN": config.user_token,
        }

    async def _dispatch_tasks(self, tasks: list[Task]) -> DispatchResponse:
        """
        Dispatches tasks for their respective directories and captures their output.
        """

        config: SLURMConfiguration = self._config

        if len(tasks) == 0:
            return DispatchResponse(
                dispatch_type="slurm",
                slurm_submission={},
                slurm_response={},
            )

        name = _resolve_slurm_job_name(tasks)
        timeout = (
            sum(task.timeout for task in tasks if task.timeout is not None)
            if any(task.timeout is not None for task in tasks)
            else None
        )
        threads = (
            max(task.threads for task in tasks if task.threads is not None)
            if any(task.threads is not None for task in tasks)
            else None
        )

        tasks_script_fragment = "\n".join(map(self._task_script_fragment, tasks))

        script = f"""#!/usr/bin/env bash

set -euo pipefail

# setup
{config.job_setup}

# tasks: {','.join(task.name for task in tasks)}

{tasks_script_fragment}
"""

        data: dict[str, Any] = {
            "job": {
                "name": name,
                **(
                    {"partition": config.partition}
                    if config.partition is not None
                    else {}
                ),
                **(
                    {
                        "nice": config.nice,
                    }
                    if config.nice is not None
                    else {}
                ),
                **(
                    {
                        "constraints": config.constraints,
                    }
                    if config.constraints is not None
                    else {}
                ),
                "time_limit": {
                    "set": timeout is not None,
                    # convert seconds -> minutes
                    "number": (timeout // 60 if timeout is not None else 0),
                },
                **({"tasks_per_node": threads} if threads is not None else {}),
                "current_working_directory": "/tmp",
                "environment": config.environment
                # add ASTRA specific environment variables for astra-web-cli
                + [
                    f"ASTRA_BINARY_PATH={config.astra_binary_path}",
                    f"ASTRA_DATA_PATH={config.data_path}",
                ],
                # separate SLURM output if desired
                "standard_output": f"{config.job_output_path}/%x-slurm-%j.out",
                "standard_error": f"{config.job_output_path}/%x-slurm-%j.err",
                "script": script,
            },
        }

        try:
            response = await self._request(
                method=RequestMethod.POST,
                midpoint="slurm",
                endpoint="job/submit",
                body=data,
            )
        except RuntimeError as e:
            raise RuntimeError(
                f"Failed to dispatch tasks {','.join(task.name for task in tasks)} to SLURM!"
            ) from e

        return DispatchResponse(
            dispatch_type="slurm",
            slurm_submission=data,
            slurm_response=response,
        )

    def _task_script_fragment(self, task: Task) -> str:
        """
        Returns the script fragment for a single task.

        Changes directory for task and captures output.
        Timing information and completion message are written to `stderr`.
        """

        quote: Callable[[str], str] = lambda s: f'"{s}"' if " " in s else s

        cmd: str = " ".join(map(quote, task.command))

        # note: `time` always writes to stderr
        script = f"""echo "{task.name}" >&2
cd '{task.cwd}'
time {cmd} > '{task.output_file_name_base}.out' 2> '{task.output_file_name_base}.err'
[ ! -s '{task.output_file_name_base}.out' ] && rm -f '{task.output_file_name_base}.out'
[ ! -s '{task.output_file_name_base}.err' ] && rm -f '{task.output_file_name_base}.err'
echo "done" >&2
"""
        return script

    async def ping(self, timeout: int | None) -> JSON:
        """
        Pings the SLURM server to check if it is reachable.

        Returns slurm ping response data.
        """
        try:
            response = await self._request(
                method=RequestMethod.GET,
                midpoint="slurm",
                endpoint="ping",
                timeout=timeout,
            )
        except RuntimeError as e:
            raise RuntimeError(f"Failed to ping SLURM.") from e
        return response

    async def diagnose(self, timeout: int | None) -> JSON:
        """
        Diagnoses the connection to SLURM.

        Returns slurm diagnose response data.
        """
        try:
            response = await self._request(
                method=RequestMethod.GET,
                midpoint="slurm",
                endpoint="diag",
                timeout=timeout,
            )
        except RuntimeError as e:
            raise RuntimeError(f"Failed to diagnose connection to SLURM.") from e
        return response

    async def _request(
        self,
        method: RequestMethod,
        midpoint: str,
        endpoint: str,
        body: JSON | None = None,
        timeout: int | None = None,
    ) -> JSON:

        config: SLURMConfiguration = self._config

        return await slurm.request(
            method=method,
            midpoint=midpoint,
            endpoint=endpoint,
            url=config.base_url,
            api_version=config.api_version,
            user_name=config.user_name,
            user_token=config.user_token,
            headers=self._header_credentials,
            body=body or {},
            timeout=timeout,
            proxy_url=config.proxy_url,
        )  # type: ignore


def _resolve_slurm_job_name(tasks: list[Task]) -> str:
    """
    Attempts to provide a meaningful name for a SLURM job consisting of multiple tasks.

    May fall back to `cummulative-tasks-<UUID>` if no good name can be found.
    """

    # idea:
    # assume name format: <prefix>-<id> where <id> is <YYYY>-<MM>-<DD>-<hh>-<mm>-<ss>-<UUID>
    # combine prefixes if all ids identical
    # else fall back to generic name

    def name_prefix_and_id(task: Task) -> tuple[str, str]:
        parts = task.name.split("-", 1)
        return (parts[0], parts[1]) if len(parts) == 2 else (task.name, "")

    prefixes_and_ids = list(map(name_prefix_and_id, tasks))

    # all ids identical
    if all(prefixes_and_ids[0][1] == pid for _, pid in prefixes_and_ids):
        return (
            ",".join(map(lambda x: x[0], prefixes_and_ids))
            + "-"
            + prefixes_and_ids[0][1]
        )

    return f"cummulative-tasks-{get_uuid()}"
