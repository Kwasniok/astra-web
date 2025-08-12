from typing import Any, Callable
import os
from enum import Enum
import requests
from .base import HostLocalizer
from .schemas.config import SLURMConfiguration
from .schemas.dispatch import DispatchResponse
from .schemas.io import JobIdsOutput


class _RequestType(Enum):

    GET = "get"
    POST = "post"
    PUT = "put"


class SLURMJobState(str, Enum):
    """
    Enum representing the possible states of a SLURM job.

    see https://slurm.schedmd.com/job_state_codes.html
    """

    BOOT_FAIL = "boot_fail"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    DEADLINE = "deadline"
    FAILED = "failed"
    NODE_FAIL = "node_fail"
    OUT_OF_MEMORY = "out_of_memory"
    PENDING = "pending"
    PREEMPTED = "preempted"
    RUNNING = "running"
    SUSPENDED = "suspended"
    TIMEOUT = "timeout"


class SLURMHostLocalizer(HostLocalizer):

    _instance = None

    @classmethod
    def instance(cls) -> "SLURMHostLocalizer":
        if cls._instance is None:
            cls._instance = SLURMHostLocalizer(do_not_init_manually_use_instance=None)

            # aquire environment variables only upon first use
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
                proxy=os.environ.get("SLURM_PROXY", None),
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
        Returns the current configuration of the SLURM host localizer.
        """
        return self._config

    @property
    def _proxies(self) -> dict[str, str] | None:
        """
        Returns the proxies used for SLURM requests.
        """
        return (
            {
                "http": self._config.proxy,
                "https": self._config.proxy,
            }
            if self._config.proxy
            else None
        )

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

    def _dispatch_command(
        self,
        name: str,
        command: list[str],
        cwd: str,
        output_file_name_base: str,
        timeout: int | None = None,
    ) -> DispatchResponse:
        """
        Dispatches a command for the specified directory and captures the output.
        """

        quote: Callable[[str], str] = lambda s: f'"{s}"' if " " in s else s

        cmd: str = " ".join(map(quote, command))

        script = f"""#!/usr/bin/env bash

set -euo pipefail

# setup
{self._config.script_setup}
# dispatched command
{cmd} > '{output_file_name_base}.out' 2> '{output_file_name_base}.err'
# finalize
status=$?
[ ! -s '{output_file_name_base}.out' ] && rm -f '{output_file_name_base}.out'
[ ! -s '{output_file_name_base}.err' ] && rm -f '{output_file_name_base}.err'
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
                    "number": timeout or 0,
                },
                "current_working_directory": cwd,
                "environment": [
                    "PATH=/bin:/usr/bin/:/usr/local/bin/",
                    "LD_LIBRARY_PATH=/lib/:/lib64/:/usr/local/lib",
                ],
                # separate SLURM output if desired
                "standard_output": f"{self._config.output_path}/{output_file_name_base}-slurm-%j.out",
                "standard_error": f"{self._config.output_path}/{output_file_name_base}-slurm-%j.err",
                "script": script,
            },
        }

        try:
            response = self._request(
                request=_RequestType.POST,
                url=f"{self._config.base_url}/slurm/{self._config.api_version}/job/submit",
                headers={
                    "Content-Type": "application/json",
                    **self._header_credentials,
                },
                json=data,
                proxies=self._proxies,
            )
        except RuntimeError as e:
            raise RuntimeError(
                f"Failed to dispatch command '{cmd}' @ '{cwd}' to SLURM"
            ) from e

        return DispatchResponse(
            dispatch_type="slurm",
            slurm_submission=data,
            slurm_response=response,
        )

    def ping(self) -> dict[str, Any]:
        """
        Pings the SLURM server to check if it is reachable.

        Returns slurm ping response data.
        """
        try:
            response = self._request(
                request=_RequestType.GET,
                url=f"{self._config.base_url}/slurm/{self._config.api_version}/ping",
                headers={
                    "Content-Type": "application/json",
                    **self._header_credentials,
                },
                proxies=self._proxies,
            )
        except RuntimeError as e:
            raise RuntimeError(f"Failed to ping SLURM.") from e
        return response

    def diagnose(self) -> dict[str, Any]:
        """
        Diagnoses the connection to SLURM.

        Returns slurm diagnose response data.
        """
        try:
            response = self._request(
                request=_RequestType.GET,
                url=f"{self._config.base_url}/slurm/{self._config.api_version}/diag",
                headers={
                    "Content-Type": "application/json",
                    **self._header_credentials,
                },
                proxies=self._proxies,
            )
        except RuntimeError as e:
            raise RuntimeError(f"Failed to diagnose connection to SLURM.") from e
        return response

    def list_jobs(self, state: set[SLURMJobState]) -> list[dict[str, Any]]:
        """
        Lists all jobs currently managed by SLURM.
        """
        data = {
            "users": self._config.user_name,
            # state: does not work due to bug in SLURM REST API
        }
        try:
            response = self._request(
                request=_RequestType.GET,
                url=f"{self._config.base_url}/slurmdb/{self._config.api_version}/jobs",
                headers={
                    "Content-Type": "application/json",
                    **self._header_credentials,
                },
                json=data,
                proxies=self._proxies,
            )
        except RuntimeError as e:
            raise RuntimeError(f"Failed to list SLURM job IDs.") from e
        # manual filtering due to bug in SLURM REST API
        jobs: list[dict[str, Any]] = response["jobs"]
        if state:
            filter: Callable[[dict[str, Any]], bool] = lambda j: bool(
                set(s.lower() for s in j["state"]["current"])
                & set(s.value for s in state)
            )
            jobs = list(j for j in jobs if filter(j))
        return jobs

    def list_job_ids(
        self, state: set[SLURMJobState], local_localizer: HostLocalizer
    ) -> JobIdsOutput:
        """
        Lists all IDs for jobs currently managed by SLURM.
        """
        job_ids = [j["name"] for j in self.list_jobs(state)]

        response = JobIdsOutput(
            particles=[
                j.removeprefix(self.GENERATE_DISPATCH_NAME_PREFIX)
                for j in job_ids
                if j.startswith(self.GENERATE_DISPATCH_NAME_PREFIX)
            ],
            simulations=[
                j.removeprefix(self.SIMULATE_DISPATCH_NAME_PREFIX)
                for j in job_ids
                if j.startswith(self.SIMULATE_DISPATCH_NAME_PREFIX)
            ],
        )

        # filter for managed ids
        gen_ids = local_localizer.generator_ids
        sim_ids = local_localizer.simulation_ids
        response.particles = [id for id in response.particles if id in gen_ids]
        response.simulations = [id for id in response.simulations if id in sim_ids]

        return response

    def _request(
        self,
        request: _RequestType,
        url: str,
        headers: dict[str, str],
        json: dict[str, Any] | None = None,
        proxies: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            match request:
                case _RequestType.GET:
                    response = requests.get(
                        url=url,
                        headers=headers,
                        json=json,
                        proxies=proxies,
                    )
                case _RequestType.POST:
                    response = requests.post(
                        url=url,
                        headers=headers,
                        json=json,
                        proxies=proxies,
                    )
                case _RequestType.PUT:
                    response = requests.put(
                        url=url,
                        headers=headers,
                        json=json,
                        proxies=proxies,
                    )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"Failed to send {request.name} request to SLURM '{url}' (user_name='{self._config.user_name}', user_token='{self._config.user_token[:4]}****{self._config.user_token[-4:]}', proxies={proxies})."
            ) from e
