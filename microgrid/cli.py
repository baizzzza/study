"""Run and record a peak measurement on a supplied import profile."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
import platform

from .inputs import IMPORT, read_series
from .peak import measure_peak
from .results import write_result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="CSV containing grid imports")
    parser.add_argument("--output", type=Path, required=True, help="Path for the JSON result")
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("Input and output must be different files")
        data = args.input.read_bytes()
        series = read_series(data)
        peak = measure_peak(series.timestamps, series.power_kw[IMPORT])
        write_result(args.output, {
            "schema_version": 1,
            "method": "maximum_supplied_grid_import",
            "python_version": platform.python_version(),
            "input_file": args.input.name,
            "input_sha256": hashlib.sha256(data).hexdigest(),
            "sample_count": len(series.timestamps),
            "peak_import_kw": peak.kw,
            "peak_timestamps_utc": [at.isoformat() for at in peak.timestamps],
        })
    except (OSError, ValueError, csv.Error) as error:
        parser.exit(2, f"error: {error}\n")


if __name__ == "__main__":
    main()
