from typing import Any
from enum import Enum
import numpy as np


class FloatPrecision(str, Enum):
    """Floating point precision."""

    FLOAT16 = "f16"
    FLOAT32 = "f32"
    FLOAT64 = "f64"
    FLOAT128 = "f128"

    @classmethod
    def select(cls, precision: str) -> "FloatPrecision":
        match precision:
            case "f16":
                return cls.FLOAT16
            case "f32":
                return cls.FLOAT32
            case "f64":
                return cls.FLOAT64
            case "f128":
                return cls.FLOAT128
            case _:
                raise ValueError(f"Unknown precision: {precision}")

    def numpy_dtype(self) -> Any:
        match self:
            case FloatPrecision.FLOAT16:
                return np.float16
            case FloatPrecision.FLOAT32:
                return np.float32
            case FloatPrecision.FLOAT64:
                return np.float64
            case FloatPrecision.FLOAT128:
                return np.float128
