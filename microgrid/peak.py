"""Measure the maximum imported power in a supplied time series."""

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Sequence


@dataclass(frozen=True)
class Peak:
    kw: float
    timestamps: tuple[datetime, ...]


def measure_peak(timestamps: Sequence[datetime], grid_import_kw: Sequence[float]) -> Peak:
    if not timestamps or len(timestamps) != len(grid_import_kw):
        raise ValueError("Timestamp and import sequences must have the same positive length")
    if any(not isfinite(value) or value < 0 for value in grid_import_kw):
        raise ValueError("Grid import must be finite and nonnegative")
    maximum = max(grid_import_kw)
    return Peak(maximum, tuple(at for at, value in zip(timestamps, grid_import_kw) if value == maximum))
