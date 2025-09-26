from typing import Any
from pydantic import BaseModel

from astra_web.generator.schemas.io import GeneratorData
from astra_web.simulation.schemas.io import SimulationDataWithMeta


class Features(BaseModel):
    """All data about a simulation run which could possibly count as a feature - e.g. including the initial particle distribution."""

    sim_id: str
    generator: GeneratorData | None
    simulation: SimulationDataWithMeta | None


FeatureTableInput = list[str]
FeatureTable = dict[str, list[Any]]
