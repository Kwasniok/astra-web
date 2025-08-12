from typing import Any
from pydantic import BaseModel

from astra_web.generator.schemas.io import GeneratorInput
from astra_web.simulation.schemas.io import (
    SimulationInput,
    SimulationData,
    SimulationMetaData,
)


class CompleteData(BaseModel):
    sim_id: str
    generator_input: GeneratorInput
    simulation_input: SimulationInput
    simulation_output: SimulationData
    simulation_meta: SimulationMetaData | None = None


FeatureTableInput = list[str]
FeatureTable = dict[str, list[Any]]
