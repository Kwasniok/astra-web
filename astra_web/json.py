import os
import json
from pydantic import BaseModel


def write_json(object: BaseModel, path: str) -> None:
    """
    Writes a Pydantic model to a JSON file.
    """

    with open(path, "w") as f:
        str_ = json.dumps(
            object.model_dump(),
            indent=4,
            sort_keys=True,
            separators=(",", ": "),
            ensure_ascii=False,
        )
        f.write(str_)
