"""Parse and validate UTF-8 CSV time series."""

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from math import isfinite

TIMESTAMP = "timestamp"
IMPORT = "grid_import_kw"
DISPATCH_COLUMNS = ("load_kw", "wind_kw", "solar_kw")
POWER_COLUMNS = (IMPORT, *DISPATCH_COLUMNS)


@dataclass(frozen=True)
class Series:
    timestamps: tuple[datetime, ...]
    power_kw: dict[str, tuple[float, ...]]


def read_series(data: bytes, required: tuple[str, ...] = (IMPORT,)) -> Series:
    reader = csv.DictReader(StringIO(data.decode("utf-8-sig"), newline=""), strict=True)
    headers = reader.fieldnames
    if not headers or len(set(headers)) != len(headers):
        raise ValueError("CSV must have a header with unique column names")
    missing = {TIMESTAMP, *required}.difference(headers)
    if missing:
        raise ValueError(f"Missing CSV columns: {', '.join(sorted(missing))}")
    columns = {name: [] for name in POWER_COLUMNS if name in headers}
    timestamps: list[datetime] = []
    for row in reader:
        line = reader.line_num
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"CSV line {line}: wrong number of fields")
        try:
            at = datetime.fromisoformat(row[TIMESTAMP].strip())
            if at.utcoffset() is None:
                raise ValueError("timestamp must include a UTC offset")
            at = at.astimezone(timezone.utc)
            if timestamps and at <= timestamps[-1]:
                raise ValueError("timestamps must be strictly increasing")
            for name, values in columns.items():
                value = float(row[name])
                if not isfinite(value) or value < 0:
                    raise ValueError(f"{name} must be finite and nonnegative")
                values.append(value)
        except ValueError as error:
            raise ValueError(f"CSV line {line}: {error}") from error
        timestamps.append(at)
    if not timestamps:
        raise ValueError("CSV must contain at least one observation")
    return Series(tuple(timestamps), {name: tuple(values) for name, values in columns.items()})
