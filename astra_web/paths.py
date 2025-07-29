import os

_ASTRA_BINARY_PATH = os.environ["ASTRA_BINARY_PATH"]

_DATA_PATH = "/app/data"
_GENERATOR_DATA_PATH = os.path.join(_DATA_PATH, "generator")
_SIMULATION_DATA_PATH = os.path.join(_DATA_PATH, "simulation")


def generator_path(id: str, extention: str = "") -> str:
    """Returns the path to the generator output for a given ID."""
    return os.path.join(_GENERATOR_DATA_PATH, id + extention)


def simulation_path(id: str, file_name: str | None = None) -> str:
    """
    Returns the path to the simulation output for a given ID.

    note: If no file_name is provided, the path to the simulation directory is returned.
          Otherwise, the path to the specific file is returned.
    """
    if file_name is not None:
        return os.path.join(_SIMULATION_DATA_PATH, id, file_name)
    return os.path.join(_SIMULATION_DATA_PATH, id)


def astra_binary_path(bin: str) -> str:
    """Returns the path to the Astra binary."""
    return os.path.join(_ASTRA_BINARY_PATH, bin)
