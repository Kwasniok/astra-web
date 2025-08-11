from typing import Annotated, Any
from pydantic import Field, conlist, field_validator
from astra_web.file import IniExportableModel


class SimulationScanQuantity(IniExportableModel):

    # web exclusive fields:
    id: int = Field(default=-1, description="The ID of the module.")

    def excluded_ini_fields(self) -> set[str]:
        return super().excluded_ini_fields() | {
            "id",
        }

    # ASTRA fields:
    name: str = Field(
        description="Name of the quantity to be scanned. See ASTRA documentation Sec. 6.3 for listing of all possible values.",
        alias="FOM",
        validation_alias="name",
    )

    def _to_ini_dict(self) -> dict[str, Any]:
        # non-excluded, non-none, aliased fields with enumeration suffixes

        out_dict = super()._to_ini_dict()
        out_dict = {f"{k}({self.id})": v for k, v in out_dict.items()}
        return out_dict


class SimulationScanSpecifications(IniExportableModel):

    # ASTRA fields:
    perform_scan: bool = Field(
        default=False,
        alias="LScan",
        validation_alias="perform_scan",
        description="If true, ASTRA will perform a scan.",
    )
    extend_scan_files: bool = Field(
        default=False,
        alias="LExtend",
        validation_alias="extend_scan_files",
        description="If true, ASTRA will extend (append) the scan files rather than overwriting them.",
    )
    scan_parameter: str = Field(
        default="",
        alias="Scan_para",
        validation_alias="scan_parameter",
        description="The parameter to be scanned",
    )
    scan_min: float | None = Field(
        default=None,
        alias="S_min",
        validation_alias="scan_min",
        description="The minimal value of the scan parameter.",
    )
    scan_max: float | None = Field(
        default=None,
        alias="S_max",
        validation_alias="scan_max",
        description="The maximal value of the scan parameter.",
    )
    scan_num: int | None = Field(
        default=None,
        alias="S_numb",
        validation_alias="scan_num",
        description="The number of scanning points.",
        gt=0,
    )
    optimize_for_min: bool = Field(
        default=False,
        alias="O_min",
        validation_alias="optimize_for_min",
        description="If true, optimize `scan_quantities[0]` for the minimal value of the scan parameter.",
    )
    optimize_for_max: bool = Field(
        default=False,
        alias="O_max",
        validation_alias="optimize_for_max",
        description="If true, optimize `scan_quantities[0]` for the maximal value of the scan parameter.",
    )
    optimize_for_match: bool = Field(
        default=False,
        alias="O_match",
        validation_alias="optimize_for_match",
        description="If true, optimize `scan_quantities[0]` to match `optimization_match_value`.",
    )
    optimization_match_value: float | None = Field(
        default=None,
        alias="match_value",
        validation_alias="optimization_match_value",
        description="The value to match when optimize_for_match is true.",
    )
    optimization_depth: int | None = Field(
        default=None,
        alias="O_depth",
        validation_alias="optimization_depth",
        description="The depth of the optimization. The total number of runs is about `scan_num`* `optimization_depth`.",
    )
    optimization_z_min: float | None = Field(
        default=None,
        alias="S_zmin",
        validation_alias="optimization_z_min",
        description="The minimal z position to be considered for the optimization.",
    )
    optimization_z_max: float | None = Field(
        default=None,
        alias="S_zmax",
        validation_alias="optimization_z_max",
        description="The maximal z position to be considered for the optimization.",
    )
    optimization_z_num: float | None = Field(
        default=None,
        alias="S_dz",
        validation_alias="optimization_z_num",
        description="The number of intervals between `optimization_z_min` and `optimization_z_max`. At each end of the interval the quantities are calculated.",
    )
    store_scanned_quantities_for_minimum: bool = Field(
        default=False,
        alias="L_min",
        validation_alias="store_scanned_quantities_for_minimum",
        description="If true, store the scanned quantities for the minimum of `scan_quantities[0]` in between `optimization_z_min`and `optimization_z_max`.",
    )
    store_scanned_quantities_for_maximun: bool = Field(
        default=False,
        alias="L_max",
        validation_alias="store_scanned_quantities_for_maximun",
        description="If true, store the scanned quantities for the maximum of `scan_quantities[0]` in between `optimization_z_min`and `optimization_z_max`.",
    )

    # converted fields:
    # note: ASTRA has an arbitrary limit of 10 items here.
    scan_quantities: Annotated[
        list[SimulationScanQuantity],
        conlist(SimulationScanQuantity, max_length=10),
    ] = Field(
        default=[],
        description="The quantity to be optimized.",
    )

    @field_validator("scan_quantities", mode="before")
    @classmethod
    def parse_scan_quantities(cls, values: Any) -> list[SimulationScanQuantity]:
        if not values:
            return []

        if not isinstance(values, list):
            raise TypeError(
                f"Invalid value for `scan_quantities`. Must be a list. Received type `{type(values)}`."
            )

        def parse_quantity(value: Any) -> SimulationScanQuantity:
            if isinstance(value, SimulationScanQuantity):
                return value
            elif isinstance(value, dict):
                return SimulationScanQuantity.model_validate(value)
            elif isinstance(value, str):
                return SimulationScanQuantity.model_validate(dict(name=value))
            else:
                raise ValueError(f"Invalid scan quantity `{value}`.")

        return list(map(parse_quantity, values))

    def _set_ids(self, attribute_key: str) -> None:
        for idx, element in enumerate(getattr(self, attribute_key), start=1):
            element.id = idx

    def model_post_init(self, __context) -> None:
        self._set_ids("scan_quantities")

    def excluded_ini_fields(self) -> set[str]:
        return super().excluded_ini_fields() | {"scan_quantities"}

    def _to_ini_dict(self) -> dict[str, Any]:
        # directly add (enumerated) scan quantities
        out = super()._to_ini_dict()
        for q in self.scan_quantities:
            out |= q._to_ini_dict()
        return out
