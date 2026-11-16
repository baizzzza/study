import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from microgrid.inputs import DISPATCH_COLUMNS, IMPORT, read_series
from microgrid.model import ModelParameters, SECTIONS
from microgrid.peak import measure_peak
from microgrid.results import write_result

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "synthetic_import.csv"


class ExperimentTests(unittest.TestCase):
    def test_peak_reports_all_ties(self):
        series = read_series(EXAMPLE.read_bytes())
        peak = measure_peak(series.timestamps, series.power_kw[IMPORT])
        self.assertEqual(peak.kw, 3.5)
        self.assertEqual(peak.timestamps, series.timestamps[1::2])

    def test_zero_peak(self):
        series = read_series(b"timestamp,grid_import_kw\n2026-01-01T00:00:00Z,0\n")
        self.assertEqual(measure_peak(series.timestamps, (0.0,)).kw, 0.0)

    def test_measurement_rejects_invalid_series(self):
        series = read_series(EXAMPLE.read_bytes())
        for values in ((0.0,), (0.0, 0.0, 0.0, float("nan"))):
            with self.subTest(values=values), self.assertRaises(ValueError):
                measure_peak(series.timestamps, values)

    def test_rejects_bad_csv(self):
        header = "timestamp,grid_import_kw\n"
        for data in (
            header,
            header + "2026-01-01T00:00:00Z,inf\n",
            header + "2026-01-01T00:00:00Z,-1\n",
            header + "2026-01-01T00:00:00Z\n",
            header + "2026-01-01T00:00:00Z,1,extra\n",
            header + "2026-01-01T00:00:00,1\n",
            header + "2026-01-01T00:00:00Z,1\n2026-01-01T08:00:00+08:00,2\n",
            "timestamp,grid_import_kw,grid_import_kw\n",
            "timestamp,net_flow\n",
        ):
            with self.subTest(data=data), self.assertRaises(ValueError):
                read_series(data.encode())

    def test_dispatch_input_columns_do_not_require_recorded_import(self):
        series = read_series(
            b"timestamp,load_kw,wind_kw,solar_kw\n2026-01-01T08:00:00+08:00,2,1,0\n",
            required=DISPATCH_COLUMNS,
        )
        self.assertEqual(series.timestamps[0].hour, 0)
        self.assertEqual(series.power_kw["wind_kw"], (1.0,))

    def test_configuration_marks_unresolved_sections(self):
        template = ROOT / "examples" / "model.pending.json"
        self.assertEqual(ModelParameters.from_json(template.read_bytes()).unresolved, SECTIONS)

    def test_configuration_rejects_invalid_schema(self):
        for data in (b"[]", b"{}", b'{"hydrogen_conversion": 12, "cost_budget": null, "dispatch_equations": null}'):
            with self.subTest(data=data), self.assertRaises(ValueError):
                ModelParameters.from_json(data)

    def test_cli_reproduces_byte_identical_result(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "results" / "peak.json"
            command = [sys.executable, "-m", "microgrid.cli", "--input", str(EXAMPLE), "--output", str(output)]
            subprocess.run(command, cwd=ROOT, check=True)
            first = output.read_bytes()
            subprocess.run(command, cwd=ROOT, check=True)
            self.assertEqual(output.read_bytes(), first)
            result = json.loads(first)
            self.assertEqual(result["sample_count"], 4)
            self.assertEqual(result["peak_import_kw"], 3.5)
            self.assertEqual(len(result["peak_timestamps_utc"]), 2)
            self.assertEqual(result["input_sha256"], hashlib.sha256(EXAMPLE.read_bytes()).hexdigest())

    def test_cli_rejects_invalid_input_without_writing_result(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "bad.csv"
            source.write_text("timestamp,grid_import_kw\n", encoding="utf-8")
            output = Path(directory) / "peak.json"
            run = subprocess.run(
                [sys.executable, "-m", "microgrid.cli", "--input", str(source), "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(run.returncode, 2)
            self.assertIn("at least one observation", run.stderr)
            self.assertFalse(output.exists())

    def test_export_preserves_previous_result_on_invalid_record(self):
        with TemporaryDirectory() as directory:
            output = Path(directory) / "peak.json"
            write_result(output, {"value": 1.0})
            original = output.read_bytes()
            with self.assertRaises(ValueError):
                write_result(output, {"value": float("nan")})
            self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
