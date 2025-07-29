import os

ASTRA_BINARY_PATH = os.environ["ASTRA_BINARY_PATH"]

DATA_PATH = "/app/data"
GENERATOR_DATA_PATH = os.path.join(DATA_PATH, "generator")
SIMULATION_DATA_PATH = os.path.join(DATA_PATH, "simulation")


def default_filename(timestamp) -> str:
    return os.path.join(GENERATOR_DATA_PATH, timestamp)