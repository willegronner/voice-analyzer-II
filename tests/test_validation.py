import unittest

from podcast_analyzer.exceptions import InvalidIdentifierError, InvalidRecordError
from podcast_analyzer.validation import (check_recording_id, check_speaker_id,
                                         parse_number, parse_speech_present,
                                         parse_timestamp, validate_session_row)

SPEAKERS = {"S001": object()}


def make_row(**changes):
    row = {
        "recording_id": "REC-2026-001", "speaker_id": "S001", "timestamp": "0",
        "speech_present": "True", "pitch": "148", "energy": "0.42", "speech_rate": "126",
        "pause_ratio": "0.19", "background_noise": "0.08", "signal_quality": "0.97",
    }
    row.update(changes)
    return row


class IdentifierTests(unittest.TestCase):
    def test_valid_identifiers(self):
        self.assertEqual(check_speaker_id("S001"), "S001")
        self.assertEqual(check_recording_id("REC-2026-001"), "REC-2026-001")

    def test_bad_speaker_ids(self):
        for value in ["001", "S01", "S0001", "s001", "S001 ", "S00A", ""]:
            with self.assertRaises(InvalidIdentifierError):
                check_speaker_id(value)

    def test_bad_recording_ids(self):
        for value in ["REC-26-102", "REC-2026-12", "REC-2026-0012", "rec-2026-001", "REC-2026-001\n"]:
            with self.assertRaises(InvalidIdentifierError):
                check_recording_id(value)


class NumberTests(unittest.TestCase):
    def test_boundary_values_are_accepted(self):
        self.assertEqual(parse_number("energy", "0", 0, 1), 0)
        self.assertEqual(parse_number("energy", "1", 0, 1), 1)
        self.assertEqual(parse_number("pitch", "45", 45, 450), 45)
        self.assertEqual(parse_number("pitch", "450", 45, 450), 450)

    def test_just_outside_the_boundary_is_rejected(self):
        with self.assertRaises(InvalidRecordError):
            parse_number("energy", "1.01", 0, 1)
        with self.assertRaises(InvalidRecordError):
            parse_number("pitch", "44.9", 45, 450)

    def test_text_and_empty_values_are_rejected(self):
        for value in ["high", "", "  ", "nan"]:
            with self.assertRaises(InvalidRecordError):
                parse_number("pitch", value, 45, 450)

    def test_timestamp(self):
        self.assertEqual(parse_timestamp("0"), 0)
        for value in ["-1", "two", "1.5", ""]:
            with self.assertRaises(InvalidRecordError):
                parse_timestamp(value)

    def test_speech_present(self):
        self.assertTrue(parse_speech_present("True"))
        self.assertFalse(parse_speech_present("False"))
        with self.assertRaises(InvalidRecordError):
            parse_speech_present("yes")


class SessionRowTests(unittest.TestCase):
    def test_valid_row_gets_real_types(self):
        cleaned = validate_session_row(make_row(), SPEAKERS)
        self.assertEqual(cleaned["timestamp"], 0)
        self.assertIs(cleaned["speech_present"], True)
        self.assertEqual(cleaned["pitch"], 148.0)

    def test_row_without_speech_keeps_no_speech_values(self):
        row = make_row(speech_present="False", pitch="", energy="", speech_rate="", pause_ratio="")
        cleaned = validate_session_row(row, SPEAKERS)
        self.assertIsNone(cleaned["pitch"])
        self.assertEqual(cleaned["signal_quality"], 0.97)

    def test_missing_pitch_while_speaking_is_rejected(self):
        with self.assertRaises(InvalidRecordError) as context:
            validate_session_row(make_row(pitch=""), SPEAKERS)
        self.assertEqual(context.exception.field, "pitch")

    def test_unknown_speaker_is_rejected(self):
        with self.assertRaises(InvalidRecordError) as context:
            validate_session_row(make_row(speaker_id="S999"), SPEAKERS)
        self.assertEqual(context.exception.field, "speaker_id")

    def test_out_of_range_signal_quality_is_rejected(self):
        with self.assertRaises(InvalidRecordError):
            validate_session_row(make_row(signal_quality="1.30"), SPEAKERS)


if __name__ == "__main__":
    unittest.main()
