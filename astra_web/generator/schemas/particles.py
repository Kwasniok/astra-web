from typing import Any
import pandas as pd
import numpy as np
from pmd_beamphysics import ParticleGroup
from typing import Type, TypeVar
from pydantic import BaseModel, ConfigDict, Field
from astra_web.file import read_csv, write_csv

T = TypeVar("T", bound=BaseModel)


class Particles(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: list[float] = Field(
        default=[],
        description="List of particle x values.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    y: list[float] = Field(
        default=[],
        description="List of particle y values",
        json_schema_extra={"format": "Unit: [m]"},
    )
    z: list[float] = Field(
        default=[],
        description="List of particle z values.",
        json_schema_extra={"format": "Unit: [m]"},
    )
    px: list[float] = Field(
        default=[],
        description="List of particle px values.",
        json_schema_extra={"format": "Unit: [eV/c]"},
    )
    py: list[float] = Field(
        default=[],
        description="List of particle py values.",
        json_schema_extra={"format": "Unit: [eV/c]"},
    )
    pz: list[float] = Field(
        default=[],
        description="List of particle pz values.",
        json_schema_extra={"format": "Unit: [eV/c]"},
    )
    t_clock: list[float] | None = []
    macro_charge: list[float] = Field(
        default=[],
        description="List of particle macro charges.",
        json_schema_extra={"format": "Unit: [nC]"},
    )
    species: list[int] | None = []
    status: list[int] | None = []

    @property
    def active_particles(self):
        return np.array(self.status) >= 0

    @property
    def lost_particles(self):
        return np.array(self.status) < 0

    def write_to_csv(self, path: str) -> None:
        write_csv(self, path)

    @classmethod
    def read_from_csv(cls: Type[T], path: str) -> T:
        return read_csv(cls, path)

    def to_df(self):
        return pd.DataFrame(self.model_dump())

    def to_pmd(
        self, ref_particle: pd.Series | None = None, only_active: bool = False
    ) -> ParticleGroup:
        """
        Returns particles as ParticleGroup object for analysis.
        """
        data = self.to_df()
        ref_particle = ref_particle if ref_particle is not None else data.iloc[0]

        if only_active:
            data = data[self.active_particles]

        data["weight"] = np.abs(data.pop("macro_charge")) * 1e-9
        data.loc[1:, "z"] = data.loc[1:, "z"] + ref_particle["z"]
        data.loc[1:, "pz"] = data.loc[1:, "pz"] + ref_particle["pz"]
        data.loc[1:, "t_clock"] = (
            data.loc[1:, "t_clock"] + ref_particle["t_clock"]
        ) * 1e-9
        data.loc[data["status"] == 1, "status"] = 2
        data.loc[data["status"] == 5, "status"] = 1

        data_dict = data.to_dict("list")
        data_dict["n_particles"] = data.size
        data_dict["species"] = "electron"
        data_dict["t"] = ref_particle["t_clock"] * 1e-9

        return ParticleGroup(data=data_dict)
