from typing import Any, Callable
import os
import slurm_requests as slurm
from slurm_requests import RequestMethod, SLURMJobState, JSON
from .base import Actor
from .schemas.any import DispatchResponse
from .schemas.slurm import (
    SLURMConfiguration,
    SLURMDispatchedJobOutput,
    SLURMDispatchedJobsOutput,
    SLURMJobOutput,
    SLURMDispatchedIDsOutput,
)


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
                    # convert seconds -> minutes
                    "number": (timeout // 60 if timeout is not None else 0),
                },
                **({"tasks_per_node": threads} if threads is not None else {}),
                "current_working_directory": cwd,
                "environment": self._config.environment,
                # separate SLURM output if desired
                "standard_output": f"{self._config.output_path}/{output_file_name_base}-slurm-%j.out",
                "standard_error": f"{self._config.output_path}/{output_file_name_base}-slurm-%j.err",
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
                f"Failed to dispatch command '{cmd}' @ '{cwd}' to SLURM"
            ) from e

        return DispatchResponse(
            dispatch_type="slurm",
            slurm_submission=data,
            slurm_response=response,
        )

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

    async def list_jobs(
        self,
        timeout: int | None,
    ) -> SLURMDispatchedJobsOutput:
        """
        Lists all jobs currently managed by SLURM.
        """

        data: JSON = {
            "users": self._config.user_name,
        }
        try:
            response = await self._request(
                method=RequestMethod.GET,
                midpoint="slurmdb",
                endpoint="jobs",
                body=data,
                timeout=timeout,
            )
        except RuntimeError as e:
            raise RuntimeError(f"Failed to list SLURM job IDs.") from e

        def extract(job: JSON) -> SLURMDispatchedJobOutput:
            id: int = job["job_id"]  # type: ignore
            partition: str | None = job.get("partition", None)  # type: ignore
            name: str = job["name"]  # type: ignore
            state: dict = job.get("state", {})  # type: ignore
            current: list[SLURMJobState] = list(
                SLURMJobState.select(s) for s in state.get("current", [])
            )
            reason: str = state.get("reason", "")  # type: ignore
            return SLURMDispatchedJobOutput(
                id=name.removeprefix(self.GENERATE_DISPATCH_NAME_PREFIX).removeprefix(
                    self.SIMULATE_DISPATCH_NAME_PREFIX
                ),
                slurm=SLURMJobOutput(
                    id=id,
                    partition=partition,
                    name=name,
                    state_current=current,
                    state_reason=reason,
                ),
            )

        def filter(jobs: list[JSON], prefix: str) -> list[JSON]:
            return [job for job in jobs if job.get("name", "").startswith(prefix)]  # type: ignore

        jobs_all: list[JSON] = response.get("jobs", [])  # type: ignore

        jobs = SLURMDispatchedJobsOutput(
            particles=[
                extract(job)
                for job in filter(jobs_all, self.GENERATE_DISPATCH_NAME_PREFIX)
            ],
            simulations=[
                extract(job)
                for job in filter(jobs_all, self.SIMULATE_DISPATCH_NAME_PREFIX)
            ],
        )

        return jobs

    async def list_dispatched_ids_by_state(
        self,
        state: SLURMJobState | None = None,
        timeout: int | None = None,
    ) -> SLURMDispatchedIDsOutput:
        """
        Lists all dispatched IDs currently managed by SLURM filtered by state.
        """

        jobs = await self.list_jobs(timeout=timeout)

        def filter_and_extract(jobs: list[SLURMDispatchedJobOutput]) -> list[str]:
            return [
                job.id
                for job in jobs
                if state is not None and state in job.slurm.state_current
            ]

        return SLURMDispatchedIDsOutput(
            particles=filter_and_extract(jobs.particles),
            simulations=filter_and_extract(jobs.simulations),
        )

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
            dry_run=None,
        )  # type: ignore
