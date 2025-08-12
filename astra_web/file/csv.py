from typing import Any, TypeVar, Type, Callable, get_origin, get_args
import os
from pydantic import BaseModel
import pandas as pd


T = TypeVar("T", bound=BaseModel)

_is_list: Callable[[Any, list[type]], bool] = (
    lambda a, types: get_origin(a) is list and get_args(a)[0] in types
)


def write(
    object: BaseModel,
    path: str,
    types: list[type] = [bool, int, float, str],
    ensure_parent_dir_exists: bool = False,
) -> None:
    """
    Writes a Pydantic model to a CSV file.

    Note: Writes only fields that are lists of the specified types.
    """

    if ensure_parent_dir_exists:
        os.makedirs(os.path.dirname(path), exist_ok=True)

    fields = object.__class__.model_fields
    pd.DataFrame(
        {
            field: getattr(object, field)
            for field, info in fields.items()
            if _is_list(info.annotation, types)
        }
    ).to_csv(path, sep=" ", header=False, index=False)


def read(cls: Type[T], path: str) -> T:
    """
    Reads a Pydantic model from a CSV file.
    """
    df = pd.read_csv(path, names=list(cls.model_fields.keys()), sep=r"\s+")
    data = df.to_dict("list")
    return cls.model_validate(data, strict=True)
