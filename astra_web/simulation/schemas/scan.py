from typing import Any
from pydantic import Field, computed_field
from astra_web.file import IniExportableModel, IniExportableValueArrayModel


class SimulationScanQuanties(IniExportableValueArrayModel[str]):

    @classmethod
    def alias(cls) -> str:
        return "FOM"


class SimulationScanSpecifications(IniExportableModel):

    def excluded_ini_fields(self) -> set[str]:
        return super().excluded_ini_fields() | {
            "scan_quantities",
        }

    # ASTRA fields:

    # loop skipped
    @computed_field(
        alias="LScan",
        description="If true, a scan will be performed. Automatically enabled when `scan_parameter` is specified.",
    )
    @property
    def scan_enable(self) -> bool:
        return self.scan_parameter is not None

    extend_scan_files: bool = Field(
        default=False,
        alias="LExtend",
        validation_alias="extend_scan_files",
        description="If true, ASTRA will extend (append) the scan files rather than overwriting them.",
    )
    scan_parameter: str | None = Field(
        default=None,
        alias="Scan_para",
        validation_alias="scan_parameter",
        description="The parameter to be scanned. If a parameter is specified, scans are performed.",
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
    optimization_z_num: int | None = Field(
        default=None,
        alias="S_dz",
        validation_alias="optimization_z_num",
        description="The number of intervals between `optimization_z_min` and `optimization_z_max`. At each end of the interval the quantities are calculated.",
    )
    # note: ASTRA has an arbitrary limit of 10 items here.
    scan_quantities: SimulationScanQuanties = Field(
        default_factory=SimulationScanQuanties,
        description="The quantities to be scanned.",
    )

    def to_ini_dict(self) -> dict[str, Any]:
        return super().to_ini_dict() | self.scan_quantities.to_ini_dict()

    def to_ini(self, indent: int = 4) -> str:
        return f"&SCAN{super().to_ini(indent=indent)}/"
