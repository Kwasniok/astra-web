from typing import Any
from pydantic import BaseModel
import json


class IniExportableModel(BaseModel):
    """
    Base model class that can be exported to INI format.

    In case the ASTRA name differs from the ASTRA web name, define the `alias` (for ASTRA) and `validation_alias` (for ASTRA web) fields.
    """

    def _to_ini_dict(self) -> dict[str, Any]:
        """
        Convert the model to a dictionary suitable for INI export.
        """
        # use `alias` for ASTRA variable names
        return self.model_dump(exclude_none=True, by_alias=True)

    def _to_ini(self, indent=4) -> str:

        s = json.dumps(
            self._to_ini_dict(),
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
        )
        return (
            s.replace('": ', " = ")
            .replace(",", "")
            .replace('  "', "  ")
            .replace('"', "'")
        )[1:-1]

    def to_ini(self) -> str:
        """
        Convert the model to an INI formatted string to be used for ASTRA.
        """
        return self._to_ini()
