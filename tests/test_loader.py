import tempfile
import unittest
from pathlib import Path

from podcast_analyzer.exceptions import DataFileError
from podcast_analyzer.loader import (count_rejected_per_session, load_sessions,
                                     load_speakers)

DATA = Path(__file__).resolve().parent.parent / "data"


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.speakers, _ = load_speakers(DATA / "speakers.csv")

    def test_speakers_are_loaded(self):
        self.assertEqual(sorted(self.speakers), ["S001", "S002", "S003"])
        self.assertEqual(self.speakers["S001"].baseline_pitch, 148.0)

    def test_valid_file_has_no_rejected_rows(self):
        sessions = {}
        accepted, rejected = load_sessions(DATA / "recording_sessions.csv", self.speakers, sessions)
        self.assertEqual(accepted, 25)
        self.assertEqual(rejected, [])
        self.assertEqual(len(sessions), 5)

    def test_invalid_file_rejects_bad_rows_and_keeps_good_ones(self):
        sessions = {}
        accepted, rejected = load_sessions(DATA / "recording_sessions_invalid.csv", self.speakers, sessions)
        self.assertEqual(accepted, 2)
        self.assertEqual(len(rejected), 9)
        first = rejected[0]
        self.assertEqual(first.source_file, "recording_sessions_invalid.csv")
        self.assertEqual(first.row_number, 3)
        self.assertEqual(first.field, "speech_present")

    def test_rejected_rows_are_counted_per_session(self):
        sessions = {}
        _, rejected = load_sessions(DATA / "recording_sessions_invalid.csv", self.speakers, sessions)
        count_rejected_per_session(sessions, rejected)
        self.assertEqual(sessions["REC-2026-101"].rejected_count, 2)

    def test_missing_file_raises_data_file_error(self):
        with self.assertRaises(DataFileError):
            load_sessions(DATA / "does_not_exist.csv", self.speakers, {})
        with self.assertRaises(DataFileError):
            load_speakers(DATA / "does_not_exist.csv")

    def test_empty_file_raises_data_file_error(self):
        with tempfile.TemporaryDirectory() as folder:
            empty = Path(folder) / "empty.csv"
            empty.write_text("", encoding="utf-8")
            with self.assertRaises(DataFileError):
                load_sessions(empty, self.speakers, {})

    def test_missing_column_rejects_rows_instead_of_crashing(self):
        with tempfile.TemporaryDirectory() as folder:
            broken = Path(folder) / "broken.csv"
            broken.write_text("recording_id,speaker_id\nREC-2026-001,S001\n", encoding="utf-8")
            accepted, rejected = load_sessions(broken, self.speakers, {})
            self.assertEqual(accepted, 0)
            self.assertEqual(len(rejected), 1)


if __name__ == "__main__":
    unittest.main()
