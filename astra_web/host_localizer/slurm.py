from typing import Any
import os
from enum import Enum
import requests
from .base import HostLocalizer
from .schemas.dispatch import DispatchResponse


class _RequestType(Enum):

    GET = "get"
    POST = "post"
    PUT = "put"


class SLURMHostLocalizer(HostLocalizer):

    _instance = None

    @classmethod
    def instance(cls) -> "SLURMHostLocalizer":
        if cls._instance is None:
            cls._instance = SLURMHostLocalizer(do_not_init_manually_use_instance=None)

            # aquire environment variables only when needed
            cls._ASTRA_BINARY_PATH = os.environ["SLURM_ASTRA_BINARY_PATH"]

            cls._DATA_PATH = os.environ["SLURM_DATA_PATH"]
            cls._GENERATOR_DATA_PATH = os.path.join(cls._DATA_PATH, "generator")
            cls._SIMULATION_DATA_PATH = os.path.join(cls._DATA_PATH, "simulation")
            # separate SLURM output if desired (relative to cwd or absolute path)
            cls._OUTPUT_PATH = os.environ.get("SLURM_OUTPUT_PATH", "")

            cls._URL = os.environ["SLURM_URL"]
            cls._PROXY = os.environ.get("SLURM_PROXY", None)
            cls._USER_NAME = os.environ["SLURM_USER_NAME"]
            cls._USER_TOKEN = os.environ["SLURM_USER_TOKEN"]
            cls._ENVIRONMENT = os.environ["SLURM_ENVIRONMENT"].split(",")

        return cls._instance

    def configure(self, user: str | None = None, token: str | None = None) -> None:
        """
        Configure the SLURM access.
        """
        if user is not None:
            self._USER_NAME = user
        if token is not None:
            self._USER_TOKEN = token

    @property
    def configuration(self) -> dict[str, Any]:
        """
        Returns the current configuration of the SLURM host localizer.
        """
        return {
            "url": self._URL,
            "proxy": self._PROXY,
            "user_name": self._USER_NAME,
            "user_token": self._USER_TOKEN,
            "environment": self._ENVIRONMENT,
        }

    @property
    def _proxies(self) -> dict[str, str] | None:
        """
        Returns the proxies used for SLURM requests.
        """
        return (
            {
                "http": self._PROXY,
                "https": self._PROXY,
            }
            if self._PROXY
            else None
        )

    @property
    def _header_credentials(self) -> dict[str, str]:
        """
        Returns the headers used for SLURM requests.
        """
        return {
            "X-SLURM-USER-NAME": self._USER_NAME,
            "X-SLURM-USER-TOKEN": self._USER_TOKEN,
        }

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
        Dispatches a command for the specified directory and captures the output.
        """

        quote = lambda s: f'"{s}"' if " " in s else s

        cmd: str = " ".join(map(quote, command))

        script = f"""#!/usr/bin/env bash

set -euo pipefail

rm -f FINISHED
        
{cmd} > '{output_file_name_base}.out' 2> '{output_file_name_base}.err'
status=$?
[ ! -s '{output_file_name_base}.out' ] && rm -f '{output_file_name_base}.out'
[ ! -s '{output_file_name_base}.err' ] && rm -f '{output_file_name_base}.err'
"""
        if confirm_finished_successfully:
            script += "if [ $status -eq 0 ]; then touch FINISHED; fi\n"

        data = {
            "job": {
                "partition": "maxcpu",
                "name": "testapi",
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
                "standard_output": f"{self._OUTPUT_PATH}/{output_file_name_base}-slurm-%j.out",
                "standard_error": f"{self._OUTPUT_PATH}/{output_file_name_base}-slurm-%j.err",
                "script": script,
            },
        }

        try:
            response = self._request(
                request=_RequestType.POST,
                url=f"{self._URL}/job/submit",
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
                url=f"{self._URL}/ping",
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
                url=f"{self._URL}/diag",
                headers={
                    "Content-Type": "application/json",
                    **self._header_credentials,
                },
                proxies=self._proxies,
            )
        except RuntimeError as e:
            raise RuntimeError(f"Failed to diagnose connection to SLURM.") from e
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
        except requests.RequestException as e:
            raise RuntimeError(
                f"Failed to send {request.name} request to SLURM '{url}' (user='{self._USER_NAME}', token='{self._USER_TOKEN[:4]}****{self._USER_TOKEN[-4:]}', proxies={proxies})."
            ) from e
