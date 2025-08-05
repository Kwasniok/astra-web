from typing import Any
import os
from enum import Enum
import requests
from .base import HostLocalizer
from .schemas.config import SLURMConfiguration
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

            # aquire environment variables only upon first use
            # avoids errors due to undefined env if SLURM is never used
            cls._config = SLURMConfiguration(
                astra_binary_path=os.environ["SLURM_ASTRA_BINARY_PATH"],
                data_path=os.environ["SLURM_DATA_PATH"],
                base_url=os.environ["SLURM_BASE_URL"],
                api_version=os.environ["SLURM_API_VERSION"],
                proxy=os.environ.get("SLURM_PROXY", None),
                user_name=os.environ["SLURM_USER_NAME"],
                user_token=os.environ["SLURM_USER_TOKEN"],
                partition=os.environ["SLURM_PARTITION"],
                constraints=os.environ.get("SLURM_CONSTRAINTS", None),
                environment=os.environ["SLURM_ENVIRONMENT"].split(","),
            )

        return cls._instance

    def configure(self, config: SLURMConfiguration) -> None:
        """
        Configure the SLURM access.
        """
        self._config = config

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
                f"Failed to send {request.name} request to SLURM '{url}' (user_name='{self._config.user_name}', user_token='{self._config.user_token[:4]}****{self._config.user_token[-4:]}', proxies={proxies})."
            ) from e
