import unittest
from pathlib import Path

from podcast_analyzer.analysis import analyze_session, classify_deviation
from podcast_analyzer.loader import count_rejected_per_session, load_sessions, load_speakers

DATA = Path(__file__).resolve().parent.parent / "data"


def analyze_all():
    speakers, _ = load_speakers(DATA / "speakers.csv")
    sessions = {}
    rejected = []
    for name in ["recording_sessions.csv", "recording_sessions_invalid.csv"]:
        rejected.extend(load_sessions(DATA / name, speakers, sessions)[1])
    count_rejected_per_session(sessions, rejected)
    return {rid: analyze_session(session) for rid, session in sessions.items()}


class DeviationTests(unittest.TestCase):
    def test_boundary_of_the_tolerance(self):
        self.assertEqual(classify_deviation(112, 100), "similar")
        self.assertEqual(classify_deviation(113, 100), "higher")
        self.assertEqual(classify_deviation(88, 100), "similar")
        self.assertEqual(classify_deviation(87, 100), "lower")

    def test_zero_reference(self):
        self.assertEqual(classify_deviation(0, 0), "similar")
        self.assertEqual(classify_deviation(1, 0), "higher")


class SessionResultTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = analyze_all()

    def test_steady_recording(self):
        self.assertEqual(self.results["REC-2026-001"]["classification"], "consistent")
        self.assertEqual(self.results["REC-2026-001"]["quality"], "high")

    def test_energetic_recording(self):
        self.assertEqual(self.results["REC-2026-002"]["classification"], "energetic")

    def test_deliberate_recording(self):
        self.assertEqual(self.results["REC-2026-003"]["classification"], "deliberate")

    def test_noisy_recording(self):
        self.assertEqual(self.results["REC-2026-004"]["classification"], "noise_affected")
        self.assertEqual(self.results["REC-2026-004"]["quality"], "low")

    def test_missing_speech_and_poor_quality(self):
        result = self.results["REC-2026-005"]
        self.assertEqual(result["classification"], "insufficient_data")
        self.assertEqual(result["usable_rows"], 0)

    def test_recording_with_mostly_rejected_rows(self):
        result = self.results["REC-2026-101"]
        self.assertEqual(result["classification"], "insufficient_data")
        self.assertEqual(result["rejected_rows"], 2)

    def test_every_result_explains_itself(self):
        for result in self.results.values():
            self.assertTrue(result["reasons"])


if __name__ == "__main__":
    unittest.main()
