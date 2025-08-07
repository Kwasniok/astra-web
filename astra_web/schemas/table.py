from pydantic import BaseModel, ConfigDict
from typing import Type, TypeVar
from astra_web.file import write_csv, read_csv

T = TypeVar("T", bound="Table")


class Table(BaseModel):
    model_config = ConfigDict(extra="forbid")

    def write_to_csv(self, path: str) -> None:
        """
        Write the table data to a CSV file.
        """
        write_csv(self, path)

    @classmethod
    def read_from_csv(cls: Type[T], path: str) -> T:
        """
        Read the table data from a CSV file.
        """
        return read_csv(cls, path)
