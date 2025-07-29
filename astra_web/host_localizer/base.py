from abc import ABC, abstractmethod


class HostLocalizer(ABC):

    def __init__(self, *, do_not_init_manually_use_instance: None):
        pass

    @classmethod
    @abstractmethod
    def instance(cls) -> "HostLocalizer":
        """
        Returns the singleton instance of the host localizer.
        """
        pass

    @abstractmethod
    def generator_path(self, id: str, extention: str = "") -> str:
        """
        Returns the path to the generator file for the given id and extension.
        """
        pass

    @abstractmethod
    def simulation_path(self, id: str, file_name: str | None = None) -> str:
        """
        Returns the path to the simulation output for a given ID.

        note: If no file_name is provided, the path to the simulation directory is returned.
            Otherwise, the path to the specific file is returned.
        """
        pass

    @abstractmethod
    def astra_binary_path(self, binary: str) -> str:
        """
        Returns the path to the Astra binary.
        """
        pass
