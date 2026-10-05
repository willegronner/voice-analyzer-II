import csv
from pathlib import Path

from .exceptions import DataFileError, InvalidIdentifierError, InvalidRecordError
from .models import AcousticObservation, RecordingSession, Speaker
from .validation import (RECORDING_ID_PATTERN, validate_session_row,
                         validate_speaker_row)


class RejectedRecord:
    def __init__(self, source_file, row_number, field, reason, recording_id=None):
        self.source_file = source_file
        self.row_number = row_number
        self.field = field
        self.reason = reason
        self.recording_id = recording_id


def read_rows(path):
    path = Path(path)
    try:
        with open(path, encoding="utf-8", newline="") as csv_file:
            reader = csv.reader(csv_file)
            header = next(reader, None)
            if header is None:
                raise DataFileError(path, "file is empty")
            for row in reader:
                if row:
                    yield reader.line_num, header, row
    except FileNotFoundError:
        raise DataFileError(path, "file not found")
    except PermissionError:
        raise DataFileError(path, "no permission to read the file")
    except UnicodeDecodeError:
        raise DataFileError(path, "file is not valid UTF-8")
    except csv.Error as error:
        raise DataFileError(path, f"could not parse csv: {error}")


def row_to_dict(header, row):
    if len(row) != len(header):
        raise InvalidRecordError("row", f"expected {len(header)} fields but found {len(row)}")
    return dict(zip(header, row))


def load_speakers(path):
    speakers = {}
    rejected = []
    for line_number, header, row in read_rows(path):
        try:
            cleaned = validate_speaker_row(row_to_dict(header, row))
            if cleaned["speaker_id"] in speakers:
                raise InvalidRecordError("speaker_id", f"'{cleaned['speaker_id']}' appears more than once")
            speakers[cleaned["speaker_id"]] = Speaker.from_row(cleaned)
        except (InvalidIdentifierError, InvalidRecordError) as error:
            rejected.append(RejectedRecord(Path(path).name, line_number, error.field, error.reason))
        except KeyError as error:
            rejected.append(RejectedRecord(Path(path).name, line_number, str(error.args[0]),
                                           "required column is missing from the file"))
    return speakers, rejected


def load_sessions(path, speakers, sessions):
    accepted = 0
    rejected = []
    for line_number, header, row in read_rows(path):
        try:
            cleaned = validate_session_row(row_to_dict(header, row), speakers)
        except (InvalidIdentifierError, InvalidRecordError) as error:
            recording_id = row[0] if RECORDING_ID_PATTERN.fullmatch(row[0]) else None
            rejected.append(RejectedRecord(Path(path).name, line_number, error.field,
                                           error.reason, recording_id))
            continue
        except KeyError as error:
            rejected.append(RejectedRecord(Path(path).name, line_number, str(error.args[0]),
                                           "required column is missing from the file"))
            continue
        recording_id = cleaned["recording_id"]
        if recording_id not in sessions:
            sessions[recording_id] = RecordingSession(recording_id, speakers[cleaned["speaker_id"]])
        sessions[recording_id].add_observation(AcousticObservation(cleaned))
        accepted += 1
    return accepted, rejected


def count_rejected_per_session(sessions, rejected_records):
    for record in rejected_records:
        if record.recording_id in sessions:
            sessions[record.recording_id].rejected_count += 1
