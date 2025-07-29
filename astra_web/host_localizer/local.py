import os
from .base import HostLocalizer


class LocalHostLocalizer(HostLocalizer):

    _ASTRA_BINARY_PATH = os.environ["ASTRA_BINARY_PATH"]

    _DATA_PATH = "/app/data"
    _GENERATOR_DATA_PATH = os.path.join(_DATA_PATH, "generator")
    _SIMULATION_DATA_PATH = os.path.join(_DATA_PATH, "simulation")

    _instance = None

    @classmethod
    def instance(cls) -> "LocalHostLocalizer":
        if cls._instance is None:
            cls._instance = LocalHostLocalizer(do_not_init_manually_use_instance=None)
        return cls._instance

    def generator_path(self, id:str, extention:str="") -> str:
        """
        Returns the path to the generator file for the given id and extension.
        """
        return os.path.join(self._GENERATOR_DATA_PATH, f"{id}{extention}")

    def simulation_path(self, id:str, file_name:str | None = None) -> str:
        """
        Returns the path to the simulation output for a given ID.

        note: If no file_name is provided, the path to the simulation directory is returned.
            Otherwise, the path to the specific file is returned.
        """
        if file_name is not None:
            return os.path.join(self._SIMULATION_DATA_PATH, id, file_name)
        return os.path.join(self._SIMULATION_DATA_PATH, id)

    def astra_binary_path(self, binary:str) -> str:
        """
        Returns the path to the Astra binary.
        """
        return os.path.join(self._ASTRA_BINARY_PATH, binary)
