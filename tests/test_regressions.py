"""Local regression checks using invented records and temporary workspaces."""
import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from evtalbert.analytics import compute_metrics, write_markdown
from evtalbert.storage import append_jsonl, export_csv, get_paths
from test_smoke import test_flow as legacy_smoke_flow


class SessionRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def add_record(self, score, state="alertness", seconds=None, outcome="success"):
        record = {
            "ts": "2025-01-01T10:00:00Z", "athlete": "synthetic-actor",
            "sport": "invented-task", "task": "documentation-fixture",
            "pre_state": state, "regulation": "invented-method",
            "sec_to_target": seconds, "obstacle": "time-pressure:synthetic",
            "outcome": outcome, "rpe": None,
            "volition": {key: score for key in (
                "purposefulness", "persistence", "self_control", "decisiveness"
            )},
            "notes": "Invented free text; identifier hashing does not remove notes.",
        }
        append_jsonl(get_paths(self.root)["logs_file"], record)

    def test_preserved_legacy_cli_smoke(self):
        legacy_smoke_flow(self.root)

    def test_three_record_metrics_and_missing_duration(self):
        self.add_record(3, seconds=20)
        self.add_record(4, state="fever", seconds=40, outcome="partial")
        self.add_record(5)
        metrics = compute_metrics(self.root)
        self.assertEqual(metrics["total_sessions"], 3)
        self.assertAlmostEqual(metrics["readiness_ratio"], 2 / 3)
        self.assertEqual(metrics["avg_sec_to_target"], 30)
        self.assertEqual(metrics["vi_series"], [3, 3.5, 4])
        self.assertEqual(metrics["outcome_counts"], {"success": 2, "partial": 1})
        self.assertEqual(metrics["top_obstacles"], [("time-pressure", 3)])

    def test_rolling_index_discards_the_eighth_oldest_rating(self):
        for score in (1, 2, 3, 4, 5, 1, 2, 3):
            self.add_record(score)
        metrics = compute_metrics(self.root)
        self.assertAlmostEqual(metrics["latest_vi"], 20 / 7)

    def test_report_has_real_markdown_lines(self):
        self.add_record(4, seconds=30)
        text = write_markdown(self.root, compute_metrics(self.root)).read_text()
        self.assertEqual(text.splitlines()[0], "# EVT‑Albert Analytics")
        self.assertIn("\n## Top Obstacles\n", text)
        self.assertNotIn("\\n", text)
        self.assertIn("- **Total sessions:** 1", text.splitlines())

    def test_empty_workspace_reports_missing_metrics_and_exports_header(self):
        metrics = compute_metrics(self.root)
        self.assertEqual(metrics["total_sessions"], 0)
        self.assertIsNone(metrics["readiness_ratio"])
        self.assertIsNone(metrics["latest_vi"])
        destination = self.root / "empty.csv"
        self.assertEqual(export_csv(self.root, destination), 0)
        with destination.open(newline="") as handle:
            reader = csv.DictReader(handle)
            self.assertIn("athlete", reader.fieldnames)
            self.assertEqual(list(reader), [])

    def test_csv_identifier_hashing_preserves_raw_logs_and_other_fields(self):
        self.add_record(3)
        self.add_record(5)
        logs = get_paths(self.root)["logs_file"]
        original_bytes = logs.read_bytes()
        plain, pseudonymous = self.root / "plain.csv", self.root / "hashed.csv"
        self.assertEqual(export_csv(self.root, plain), 2)
        self.assertEqual(export_csv(self.root, pseudonymous, anonymize_names=True), 2)
        with plain.open(newline="") as handle:
            plain_rows = list(csv.DictReader(handle))
        with pseudonymous.open(newline="") as handle:
            hashed_rows = list(csv.DictReader(handle))
        self.assertEqual(plain_rows[0]["athlete"], "synthetic-actor")
        self.assertNotEqual(hashed_rows[0]["athlete"], "synthetic-actor")
        self.assertEqual(hashed_rows[0]["athlete"], hashed_rows[1]["athlete"])
        self.assertEqual(hashed_rows[0]["notes"], plain_rows[0]["notes"])
        self.assertEqual(logs.read_bytes(), original_bytes)

    def test_bad_rating_does_not_append_a_record(self):
        arguments = [
            sys.executable, "-m", "evtalbert.cli", "log-session",
            "--athlete", "synthetic-actor", "--sport", "invented-task",
            "--task", "fixture", "--pre-state", "alertness",
            "--regulation", "invented", "--obstacle", "invented",
            "--outcome", "success", "--v", "purposefulness=invalid",
            "--root", str(self.root),
        ]
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Non-integer volition score", result.stderr)
        self.assertFalse(get_paths(self.root)["logs_file"].exists())


if __name__ == "__main__":
    unittest.main()
