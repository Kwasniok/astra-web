import os
import requests
from .base import HostLocalizer
from .schemas.dispatch import DispatchResponse


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
    ) -> DispatchResponse:
        """
        Dispatches a command for the specified directory and captures the output.
        """

        quote = lambda s: f'"{s}"' if " " in s else s

        cmd: str = " ".join(map(quote, command))
        url = f"{self._URL}/job/submit"
        headers = {
            "Content-Type": "application/json",
            "X-SLURM-USER-NAME": self._USER_NAME,
            "X-SLURM-USER-TOKEN": self._USER_TOKEN,
        }
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
                "script": f"""#!/usr/bin/env bash
{cmd} > '{output_file_name_base}.out' 2> '{output_file_name_base}.err'
[ ! -s '{output_file_name_base}.out' ] && rm -f '{output_file_name_base}.out'
[ ! -s '{output_file_name_base}.err' ] && rm -f '{output_file_name_base}.err'
""",
            },
        }
        proxies = (
            {
                "http": self._PROXY,
                "https": self._PROXY,
            }
            if self._PROXY
            else None
        )

        try:
            response = requests.post(
                url=url,
                headers=headers,
                json=data,
                proxies=proxies,
            )
        except requests.RequestException as e:
            raise RuntimeError(
                f"Failed to dispatch command '{cmd}' @ '{cwd}' to SLURM '{url}' (user='{self._USER_NAME}', proxies={proxies})."
            ) from e

        if response.status_code != 200:
            raise RuntimeError(
                f"Failed to dispatch command to SLURM '{url}' (user='{self._USER_NAME}', proxies={proxies}, response_status={response.status_code})\n\n{data=}\n\nresponse_text='{response.text}'"
            )

        return DispatchResponse(
            dispatch_type="slurm",
            slurm_submission=data,
            slurm_response=response.json(),
        )
