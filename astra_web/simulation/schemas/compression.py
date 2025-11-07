from pydantic import BaseModel, Field
from astra_web.dtypes import FloatPrecision


class CompressionConfig(BaseModel):
    """Configuration for (un-)compression of simulation data files."""

    precision: FloatPrecision = Field(
        default=FloatPrecision.FLOAT64,
        description="Precision level for compression (e.g., 'f32', 'f64').",
    )
    max_rel_err: float = Field(
        default=1e-4,
        description="Maximum relative error per element allowed during compression.",
    )


class CompressionReport(BaseModel):
    """Summary for successful (un-)compression."""

    original_files: list[str] = Field(
        ...,
        description="List of original file names that were compressed.",
    )
    new_files: list[str] = Field(
        ...,
        description="List of new file names.",
    )
    total_original_size: int = Field(
        ...,
        description="Total size of original files in bytes.",
    )
    total_new_size: int = Field(
        ...,
        description="Total size of compressed files in bytes.",
    )
    compression_ratio: float = Field(
        ...,
        description="Overall compression ratio (`total_original_size / total_new_size`).",
    )
