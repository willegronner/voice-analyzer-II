import re

from .exceptions import InvalidIdentifierError, InvalidRecordError

SPEAKER_ID_PATTERN = re.compile(r"S\d{3}")
RECORDING_ID_PATTERN = re.compile(r"REC-\d{4}-\d{3}")

NUMBER_RANGES = {
    "pitch": (45, 450),
    "energy": (0, 1),
    "speech_rate": (30, 260),
    "pause_ratio": (0, 1),
    "background_noise": (0, 1),
    "signal_quality": (0, 1),
}

BASELINE_FIELDS = {
    "baseline_pitch": "pitch",
    "baseline_energy": "energy",
    "baseline_speech_rate": "speech_rate",
    "baseline_pause_ratio": "pause_ratio",
}


def check_speaker_id(value):
    if not SPEAKER_ID_PATTERN.fullmatch(value):
        raise InvalidIdentifierError("speaker_id", value, "S followed by three digits")
    return value


def check_recording_id(value):
    if not RECORDING_ID_PATTERN.fullmatch(value):
        raise InvalidIdentifierError("recording_id", value, "REC-YYYY-NNN")
    return value


def parse_number(field, text, lower, upper):
    if text.strip() == "":
        raise InvalidRecordError(field, "value is missing")
    try:
        number = float(text)
    except ValueError:
        raise InvalidRecordError(field, f"'{text}' is not a number")
    if not (lower <= number <= upper):
        raise InvalidRecordError(field, f"{number} is outside the range {lower} to {upper}")
    return number


def parse_timestamp(text):
    try:
        timestamp = int(text)
    except ValueError:
        raise InvalidRecordError("timestamp", f"'{text}' is not a whole number")
    if timestamp < 0:
        raise InvalidRecordError("timestamp", f"{timestamp} is negative")
    return timestamp


def parse_speech_present(text):
    value = text.strip().lower()
    if value == "true":
        return True
    if value == "false":
        return False
    raise InvalidRecordError("speech_present", f"'{text}' is not True or False")


def validate_speaker_row(row):
    check_speaker_id(row["speaker_id"])
    if row["name"].strip() == "":
        raise InvalidRecordError("name", "value is missing")
    cleaned = {"speaker_id": row["speaker_id"], "name": row["name"].strip()}
    for field, number_field in BASELINE_FIELDS.items():
        lower, upper = NUMBER_RANGES[number_field]
        cleaned[field] = parse_number(field, row[field], lower, upper)
    return cleaned


def validate_session_row(row, known_speakers):
    check_recording_id(row["recording_id"])
    check_speaker_id(row["speaker_id"])
    try:
        known_speakers[row["speaker_id"]]
    except KeyError:
        raise InvalidRecordError("speaker_id", f"unknown speaker '{row['speaker_id']}'")

    cleaned = {
        "recording_id": row["recording_id"],
        "speaker_id": row["speaker_id"],
        "timestamp": parse_timestamp(row["timestamp"]),
        "speech_present": parse_speech_present(row["speech_present"]),
    }
    for field in ("pitch", "energy", "speech_rate", "pause_ratio"):
        lower, upper = NUMBER_RANGES[field]
        if cleaned["speech_present"]:
            cleaned[field] = parse_number(field, row[field], lower, upper)
        else:
            cleaned[field] = None
    for field in ("background_noise", "signal_quality"):
        lower, upper = NUMBER_RANGES[field]
        cleaned[field] = parse_number(field, row[field], lower, upper)
    return cleaned
