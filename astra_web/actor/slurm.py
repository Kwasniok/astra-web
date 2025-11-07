from typing import Any, Callable
import os
import slurm_requests as slurm
from slurm_requests import RequestMethod, JSON
from .base import Actor, Task
from .schemas.any import DispatchResponse
from .schemas.slurm import SLURMConfiguration
from astra_web.uuid import get_uuid


class SLURMActor(Actor):

    _instance = None

    @classmethod
    def instance(cls) -> "SLURMActor":
        if cls._instance is None:
            cls._instance = SLURMActor(do_not_init_manually_use_instance=None)

            # acquire environment variables only upon first use
            # avoids errors due to undefined env if SLURM is never used
            split: Callable[[str | None], list[str]] = lambda csv: (
                csv.split(",") if csv else []
            )
            cls._config = SLURMConfiguration(
                astra_binary_path=os.environ["SLURM_ASTRA_BINARY_PATH"],
                data_path=os.environ["SLURM_DATA_PATH"],
                output_path=os.environ.get("SLURM_OUTPUT_PATH", "."),
                base_url=os.environ["SLURM_BASE_URL"],
                api_version=os.environ["SLURM_API_VERSION"],
                proxy_url=os.environ.get("SLURM_PROXY_URL", None),
                user_name=os.environ["SLURM_USER_NAME"],
                user_token=os.environ["SLURM_USER_TOKEN"],
                partition=os.environ["SLURM_PARTITION"],
                constraints=os.environ.get("SLURM_CONSTRAINTS", None),
                environment=split(os.environ.get("SLURM_ENVIRONMENT", None)),
                script_setup=os.environ.get("SLURM_SCRIPT_SETUP", ""),
            )

        return cls._instance

    def configure(self, config: SLURMConfiguration) -> None:
        """
        Configure the SLURM access.
        """
        self._config = config

    def update_user_token(self, user_token: str) -> None:
        """
        Update the SLURM user token.
        """
        self._config.user_token = user_token

    @property
    def configuration(self) -> SLURMConfiguration:
        """
        Returns the current configuration of the SLURM host actor.
        """
        return self._config

    @property
    def _header_credentials(self) -> dict[str, str]:
        """
        Returns the headers used for SLURM requests.
        """
        return {
            "X-SLURM-USER-NAME": self._config.user_name,
            "X-SLURM-USER-TOKEN": self._config.user_token,
        }

    def data_path(self) -> str:
        return self._config.data_path

    def astra_binary_path(self, binary: str) -> str:
        """
        Returns the path to the Astra binary.
        """
        return os.path.join(self._config.astra_binary_path, binary)

    async def _dispatch_tasks(self, tasks: list[Task]) -> DispatchResponse:
        """
        Dispatches tasks for their respective directories and captures their output.
        """

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
{self._config.script_setup}

# tasks: {','.join(task.name for task in tasks)}

{tasks_script_fragment}
"""

        data: dict[str, Any] = {
            "job": {
                "name": name,
                "partition": self._config.partition,
                **(
                    {
                        "constraints": self._config.constraints,
                    }
                    if self._config.constraints is not None
                    else {}
                ),
                "time_limit": {
                    "set": timeout is not None,
                    # convert seconds -> minutes
                    "number": (timeout // 60 if timeout is not None else 0),
                },
                **({"tasks_per_node": threads} if threads is not None else {}),
                "current_working_directory": "/tmp",
                "environment": self._config.environment
                # add ASTRA specific environment variables for astra-web-cli
                + [
                    f"ASTRA_BINARY_PATH={self._config.astra_binary_path}",
                    f"ASTRA_DATA_PATH={self._config.data_path}",
                ],
                # separate SLURM output if desired
                "standard_output": f"{self._config.output_path}/%x-slurm-%j.out",
                "standard_error": f"{self._config.output_path}/%x-slurm-%j.err",
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

        return await slurm.request(
            method=method,
            midpoint=midpoint,
            endpoint=endpoint,
            url=self._config.base_url,
            api_version=self._config.api_version,
            user_name=self._config.user_name,
            user_token=self._config.user_token,
            headers=self._header_credentials,
            body=body or {},
            timeout=timeout,
            proxy_url=self._config.proxy_url,
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
