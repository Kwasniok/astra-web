from typing import TypeVar, Type
import os
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

JSONType = None | bool | int | float | str | list["JSONType"] | dict[str, "JSONType"]


def write(
    object: BaseModel,
    path: str,
    ensure_parent_dir_exists: bool = False,
) -> None:
    """
    Writes a Pydantic model to a JSON file.

    note: Uses original names or validation_alias and no alias. Skips computed fields.
    """

    if ensure_parent_dir_exists:
        os.makedirs(os.path.dirname(path), exist_ok=True)

    # note: Alias is reserved for ASTRA names onl. Use original names/validation_alias instead.
    # skip computed fields via `round_trip=True`
    s = object.model_dump_json(by_alias=False, round_trip=True, indent=4)
    with open(path, "w") as f:
        f.write(s)


def read(cls: Type[T], path: str) -> T:
    """
    Reads a Pydantic model from a JSON file.
    """
    with open(path, "r") as f:
        s = f.read()
    return cls.model_validate_json(s, strict=True)
