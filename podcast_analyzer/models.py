from statistics import mean

from .exceptions import InvalidRecordError
from .validation import NUMBER_RANGES

MIN_SIGNAL_QUALITY = 0.5


class Speaker:
    def __init__(self, speaker_id, name, baseline_pitch, baseline_energy,
                 baseline_speech_rate, baseline_pause_ratio):
        self.speaker_id = speaker_id
        self.name = name
        self._baseline_pitch = None
        self.baseline_pitch = baseline_pitch
        self.baseline_energy = baseline_energy
        self.baseline_speech_rate = baseline_speech_rate
        self.baseline_pause_ratio = baseline_pause_ratio

    @property
    def baseline_pitch(self):
        return self._baseline_pitch

    @baseline_pitch.setter
    def baseline_pitch(self, value):
        lower, upper = NUMBER_RANGES["pitch"]
        if not (lower <= value <= upper):
            raise InvalidRecordError("baseline_pitch", f"{value} is outside the range {lower} to {upper}")
        self._baseline_pitch = value

    @classmethod
    def from_row(cls, row):
        return cls(
            speaker_id=row["speaker_id"],
            name=row["name"],
            baseline_pitch=row["baseline_pitch"],
            baseline_energy=row["baseline_energy"],
            baseline_speech_rate=row["baseline_speech_rate"],
            baseline_pause_ratio=row["baseline_pause_ratio"],
        )


class AcousticObservation:
    def __init__(self, row):
        self.timestamp = row["timestamp"]
        self.speech_present = row["speech_present"]
        self.pitch = row["pitch"]
        self.energy = row["energy"]
        self.speech_rate = row["speech_rate"]
        self.pause_ratio = row["pause_ratio"]
        self.background_noise = row["background_noise"]
        self.signal_quality = row["signal_quality"]

    @property
    def is_usable(self):
        return self.speech_present and self.signal_quality >= MIN_SIGNAL_QUALITY

    @property
    def is_low_quality(self):
        return self.speech_present and self.signal_quality < MIN_SIGNAL_QUALITY


class RecordingSession:
    def __init__(self, recording_id, speaker):
        self.recording_id = recording_id
        self.speaker = speaker
        self.observations = []
        self.rejected_count = 0

    def add_observation(self, observation):
        self.observations.append(observation)

    @property
    def total_count(self):
        return len(self.observations) + self.rejected_count

    def usable_observations(self):
        return [obs for obs in self.observations if obs.is_usable]

    @property
    def usable_count(self):
        return len(self.usable_observations())

    @property
    def no_speech_count(self):
        return len([obs for obs in self.observations if not obs.speech_present])

    @property
    def low_quality_count(self):
        return len([obs for obs in self.observations if obs.is_low_quality])

    @property
    def usable_ratio(self):
        if self.total_count == 0:
            return 0
        return self.usable_count / self.total_count

    def summary_for(self, feature_name, only_usable=True):
        source = self.usable_observations() if only_usable else self.observations
        values = [getattr(obs, feature_name) for obs in source]
        values = [v for v in values if v is not None]
        if not values:
            return None
        return {
            "average": round(mean(values), 2),
            "minimum": round(min(values), 2),
            "maximum": round(max(values), 2),
        }
