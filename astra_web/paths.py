import os

ASTRA_BINARY_PATH = os.environ["ASTRA_BINARY_PATH"]

DATA_PATH = "/app/data"
GENERATOR_DATA_PATH = os.path.join(DATA_PATH, "generator")
SIMULATION_DATA_PATH = os.path.join(DATA_PATH, "simulation")


def generator_base_path(id: str) -> str:
    return os.path.join(GENERATOR_DATA_PATH, id)

def simulation_base_path(id: str) -> str:
    return os.path.join(SIMULATION_DATA_PATH, id)