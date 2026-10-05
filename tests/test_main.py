import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_program(*arguments):
    return subprocess.run([sys.executable, "main.py", *arguments], cwd=ROOT,
                          capture_output=True, text=True)


class ProgramTests(unittest.TestCase):
    def test_creates_output_folder_and_files(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "new" / "output"
            result = run_program("--output", str(output))
            self.assertEqual(result.returncode, 0)
            for name in ["analysis_summary.csv", "analysis_report.txt", "rejected_records.txt"]:
                self.assertTrue((output / name).exists())

    def test_running_twice_gives_the_same_files(self):
        with tempfile.TemporaryDirectory() as folder:
            run_program("--output", folder)
            first = {p.name: p.read_text(encoding="utf-8") for p in Path(folder).iterdir()}
            run_program("--output", folder)
            second = {p.name: p.read_text(encoding="utf-8") for p in Path(folder).iterdir()}
            self.assertEqual(first, second)

    def test_missing_profile_file_stops_with_error(self):
        with tempfile.TemporaryDirectory() as folder:
            result = run_program("--profiles", "data/nope.csv", "--output", folder)
            self.assertEqual(result.returncode, 1)
            self.assertIn("file not found", result.stderr)

    def test_missing_session_file_is_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            result = run_program("--sessions", "data/nope.csv", "data/recording_sessions.csv",
                                 "--output", folder)
            self.assertEqual(result.returncode, 0)
            self.assertIn("Skipping file", result.stderr)
            self.assertIn("Accepted rows: 25", result.stdout)


if __name__ == "__main__":
    unittest.main()
