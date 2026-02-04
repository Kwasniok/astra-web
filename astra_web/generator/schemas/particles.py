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
    t_clock: list[float] = Field(
        default=[],
        description="List of particle time values.",
        json_schema_extra={"format": "Unit: [ns]"},
    )
    macro_charge: list[float] = Field(
        default=[],
        description="List of particle macro charges.",
        json_schema_extra={"format": "Unit: [nC]"},
    )
    species: list[int] = Field(
        default=[],
        description=r"List of species specifications:\n1\telectrons\n2\tpositrons\n3\tprotons\n4\tH-ions\n5-14\tuser defined mass-charge-ratios",
    )
    status_flag: list[int] = Field(
        default=[],
        description=r"List of particle ASTRA status flags:\nsee ATRA manual for details",
    )

    @property
    def active_particles(self):
        return np.array(self.status_flag) >= 0

    @property
    def lost_particles(self):
        return np.array(self.status_flag) < 0

    def write_to_csv(self, path: str) -> None:
        write_csv(self, path)

    @classmethod
    def read_from_csv(cls: Type[T], path: str) -> T:
        return read_csv(cls, path)

    @classmethod
    def from_array(cls: Type[T], array: np.typing.NDArray) -> T:
        """
        Create Particles instance from numpy array.

        - Index: `[<row>, <col>]`
        """
        # prefer hard coded fields to avoid issues with pydantic introspection
        columns = [
            ("x", float),
            ("y", float),
            ("z", float),
            ("px", float),
            ("py", float),
            ("pz", float),
            ("t_clock", float),
            ("macro_charge", float),
            ("species", int),
            ("status_flag", int),
        ]
        return cls(
            **{
                col: array[:, i].astype(dtype).tolist()
                for i, (col, dtype) in enumerate(columns)
            }
        )

    def to_df(self):
        return pd.DataFrame(self.model_dump())

    def to_pmd(
        self, ref_particle: pd.Series | None = None, include_inactive: bool = False
    ) -> ParticleGroup:
        """
        Returns particles as ParticleGroup object for analysis.
        """
        data = self.to_df()
        ref_particle = ref_particle if ref_particle is not None else data.iloc[0]

        if not include_inactive:
            data = data[self.active_particles]

        data["weight"] = np.abs(data.pop("macro_charge")) * 1e-9
        data.loc[1:, "z"] = data.loc[1:, "z"] + ref_particle["z"]
        data.loc[1:, "pz"] = data.loc[1:, "pz"] + ref_particle["pz"]
        data.loc[1:, "t_clock"] = (
            data.loc[1:, "t_clock"] + ref_particle["t_clock"]
        ) * 1e-9
        data.loc[data["status_flag"] == 1, "status"] = 2
        data.loc[data["status_flag"] == 5, "status"] = 1

        data_dict = data.to_dict("list")
        data_dict["n_particles"] = data.size
        data_dict["species"] = "electron"
        data_dict["t"] = ref_particle["t_clock"] * 1e-9

        return ParticleGroup(data=data_dict)
