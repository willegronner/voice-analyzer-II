import csv
from pathlib import Path

from .exceptions import DataFileError

SUMMARY_COLUMNS = [
    "recording_id", "speaker_id", "classification", "quality", "accepted_rows",
    "rejected_rows", "usable_rows", "usable_ratio", "avg_pitch", "avg_energy",
    "avg_speech_rate", "avg_pause_ratio", "avg_background_noise", "avg_signal_quality",
]

FEATURES = ["pitch", "energy", "speech_rate", "pause_ratio", "background_noise", "signal_quality"]


def average_or_blank(result, feature):
    summary = result["summaries"][feature]
    return "" if summary is None else summary["average"]


def write_summary_csv(results, path):
    with open(path, "w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(SUMMARY_COLUMNS)
        for result in results:
            writer.writerow([
                result["recording_id"], result["speaker_id"], result["classification"],
                result["quality"], result["accepted_rows"], result["rejected_rows"],
                result["usable_rows"], result["usable_ratio"],
            ] + [average_or_blank(result, feature) for feature in FEATURES])


def format_analysis_report(results):
    lines = ["Analysis report", "================", ""]
    for result in results:
        lines.append(f"{result['recording_id']} - {result['speaker_name']} ({result['speaker_id']})")
        lines.append(f"  Classification: {result['classification']}")
        lines.append(f"  Recording quality: {result['quality']}")
        lines.append("  Why:")
        for reason in result["reasons"]:
            lines.append(f"    - {reason}")
        lines.append("")
    return "\n".join(lines)


def format_rejected_report(rejected_records):
    lines = ["Rejected records", "================", ""]
    if not rejected_records:
        lines.append("No rows were rejected.")
    for record in rejected_records:
        lines.append(f"{record.source_file}, row {record.row_number}, "
                     f"field '{record.field}': {record.reason}")
    lines.append("")
    lines.append(f"Total rejected rows: {len(rejected_records)}")
    return "\n".join(lines) + "\n"


def write_reports(results, rejected_records, output_dir):
    output_dir = Path(output_dir)
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        summary_path = output_dir / "analysis_summary.csv"
        report_path = output_dir / "analysis_report.txt"
        rejected_path = output_dir / "rejected_records.txt"
        write_summary_csv(results, summary_path)
        report_path.write_text(format_analysis_report(results), encoding="utf-8")
        rejected_path.write_text(format_rejected_report(rejected_records), encoding="utf-8")
    except PermissionError:
        raise DataFileError(output_dir, "no permission to write the reports")
    except OSError as error:
        raise DataFileError(output_dir, f"could not write the reports: {error}")
    return [summary_path, report_path, rejected_path]
