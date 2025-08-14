from typing import Any, TypeVar, Generic, Callable, cast
from abc import ABC, abstractmethod
from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator
from functools import reduce
import json


class IniExportableModel(BaseModel):
    """
    Base model class that can be exported to INI format.

    In case the ASTRA name differs from the ASTRA web name, define the `alias` (for ASTRA) and `validation_alias` (for ASTRA web) fields.
    """

    model_config = ConfigDict(
        extra="forbid",
        validate_by_name=True,
        use_enum_values=True,
    )

    def excluded_ini_fields(self) -> set[str]:
        """
        Returns a set of fields that should be excluded from the INI export.
        """
        return set()

    def to_ini_dict(self) -> dict[str, Any]:
        """
        Convert the model to a dictionary suitable for INI export.
        """
        # use `alias` for ASTRA variable names
        return self.model_dump(
            exclude_none=True, by_alias=True, exclude=self.excluded_ini_fields()
        )

    def to_ini(self, indent: int = 4) -> str:
        """
        Convert the model to an INI formatted string to be used for ASTRA.
        """

        s = json.dumps(
            self.to_ini_dict(),
            indent=indent,
            sort_keys=False,
            ensure_ascii=False,
        )
        return (
            s.replace('": ', " = ")
            .replace(",", "")
            .replace('  "', "  ")
            .replace('"', "'")
        )[1:-1]


IEM = TypeVar("IEM", bound="IniExportableModel")


class IniExportableArrayModel(IniExportableModel, Generic[IEM]):
    """
    Array of models to be exported to INI format with automatic enumeration.
    """

    values: list[IEM] = Field(default_factory=list[IEM])

    def excluded_ini_fields(self) -> set[str]:
        return super().excluded_ini_fields() | {
            "values",
        }

    def to_ini_dict(self) -> dict[str, Any]:
        # non-excluded, non-none, aliased fields with enumeration suffixes

        out_dicts = [
            {f"{k}({n})": v for k, v in elem.to_ini_dict().items()}
            for n, elem in enumerate(self.values, start=1)
        ]
        union: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] = (
            lambda a, b: {**a, **b}
        )
        return reduce(union, out_dicts, {})

    @model_validator(mode="before")
    @classmethod
    def _from(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return cast(dict[str, Any], value)
        return dict(values=value)

    @model_serializer(mode="plain")
    def _to(self) -> list[IEM]:
        return self.values


T = TypeVar("T")


class IniExportableValueArrayModel(ABC, IniExportableModel, Generic[T]):
    """
    Array of values to be exported to INI format with automatic enumeration.
    """

    values: list[T] = Field(default_factory=lambda: list[T]())

    @classmethod
    @abstractmethod
    def alias(cls) -> str:
        pass

    def excluded_ini_fields(self) -> set[str]:
        return super().excluded_ini_fields() | {
            "values",
        }

    def to_ini_dict(self) -> dict[str, Any]:
        return {
            f"{self.__class__.alias()}({n})": v
            for n, v in enumerate(self.values, start=1)
        }

    @model_validator(mode="before")
    @classmethod
    def _from(cls, value: Any) -> Any:
        if isinstance(value, dict):
            return cast(dict[str, Any], value)
        return dict(values=value)

    @model_serializer(mode="plain")
    def _to(self) -> list[T]:
        return self.values
