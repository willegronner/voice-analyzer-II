MIN_USABLE_WINDOWS = 3
MIN_USABLE_RATIO = 0.4
MAX_NOISE = 0.45


def classify_deviation(measured, reference, tolerance=0.12):
    if reference == 0:
        return "similar" if measured == 0 else "higher"
    change = (measured - reference) / reference
    if change > tolerance:
        return "higher"
    if change < -tolerance:
        return "lower"
    return "similar"


def classify_session(directions, noise_ok, enough_data):
    pitch, energy, rate, pause = directions
    if not enough_data:
        return "insufficient_data"
    if not noise_ok:
        return "noise_affected"
    if pitch == energy == rate == pause == "similar":
        return "consistent"
    if energy == "higher" and rate == "higher" and pause == "lower":
        return "energetic"
    if energy == "lower" and rate == "lower" and pause == "higher":
        return "deliberate"
    return "temporarily_varied"


def evaluate_quality(quality_summary, rejected_count, enough_data):
    if quality_summary is None or not enough_data:
        return "low"
    if quality_summary["average"] >= 0.85 and rejected_count == 0:
        return "high"
    if quality_summary["average"] >= 0.65:
        return "medium"
    return "low"


def analyze_session(session):
    speaker = session.speaker
    summaries = {
        "pitch": session.summary_for("pitch"),
        "energy": session.summary_for("energy"),
        "speech_rate": session.summary_for("speech_rate"),
        "pause_ratio": session.summary_for("pause_ratio"),
        "background_noise": session.summary_for("background_noise", only_usable=False),
        "signal_quality": session.summary_for("signal_quality", only_usable=False),
    }
    baselines = {
        "pitch": speaker.baseline_pitch,
        "energy": speaker.baseline_energy,
        "speech_rate": speaker.baseline_speech_rate,
        "pause_ratio": speaker.baseline_pause_ratio,
    }

    enough_data = (session.usable_count >= MIN_USABLE_WINDOWS
                   and session.usable_ratio >= MIN_USABLE_RATIO)

    directions = {}
    if enough_data:
        for feature, baseline in baselines.items():
            directions[feature] = classify_deviation(summaries[feature]["average"], baseline)

    noise_ok = True
    if summaries["background_noise"] is not None:
        noise_ok = (summaries["background_noise"]["average"] <= MAX_NOISE
                    and summaries["signal_quality"]["average"] >= 0.65)

    if enough_data:
        classification = classify_session(tuple(directions.values()), noise_ok, enough_data)
    else:
        classification = "insufficient_data"
    quality = evaluate_quality(summaries["signal_quality"], session.rejected_count, enough_data)

    reasons = [f"usable rows: {session.usable_count} of {session.total_count} "
               f"({round(session.usable_ratio * 100)}%)"]
    if session.rejected_count:
        reasons.append(f"rejected rows for this recording: {session.rejected_count}")
    if session.no_speech_count:
        reasons.append(f"windows without speech: {session.no_speech_count}")
    if session.low_quality_count:
        reasons.append(f"windows with signal quality below 0.5 (left out of the averages): "
                       f"{session.low_quality_count}")
    if not enough_data:
        reasons.append(f"at least {MIN_USABLE_WINDOWS} usable windows and a usable ratio of "
                       f"{MIN_USABLE_RATIO} are needed for a classification")
    else:
        for feature, direction in directions.items():
            reasons.append(f"{feature} averaged {summaries[feature]['average']} "
                           f"against a usual {baselines[feature]} ({direction})")
        reasons.append(f"average background noise {summaries['background_noise']['average']} "
                       f"(limit {MAX_NOISE}), average signal quality "
                       f"{summaries['signal_quality']['average']}")

    return {
        "recording_id": session.recording_id,
        "speaker_id": speaker.speaker_id,
        "speaker_name": speaker.name,
        "classification": classification,
        "quality": quality,
        "accepted_rows": len(session.observations),
        "rejected_rows": session.rejected_count,
        "usable_rows": session.usable_count,
        "usable_ratio": round(session.usable_ratio, 2),
        "summaries": summaries,
        "directions": directions,
        "reasons": reasons,
    }
