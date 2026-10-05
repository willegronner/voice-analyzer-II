import argparse
import sys

from podcast_analyzer.analysis import analyze_session
from podcast_analyzer.exceptions import DataFileError
from podcast_analyzer.loader import (count_rejected_per_session, load_sessions,
                                     load_speakers)
from podcast_analyzer.reporting import write_reports


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profiles", default="data/speakers.csv")
    parser.add_argument("--sessions", nargs="+",
                        default=["data/recording_sessions.csv", "data/recording_sessions_invalid.csv"])
    parser.add_argument("--output", default="output")
    return parser.parse_args()


def main():
    args = parse_arguments()

    try:
        speakers, rejected = load_speakers(args.profiles)
    except DataFileError as error:
        print(f"Cannot continue without speaker profiles - {error}", file=sys.stderr)
        return 1

    sessions = {}
    accepted_rows = 0
    for session_file in args.sessions:
        try:
            accepted, rejected_in_file = load_sessions(session_file, speakers, sessions)
        except DataFileError as error:
            print(f"Skipping file - {error}", file=sys.stderr)
            continue
        accepted_rows += accepted
        rejected.extend(rejected_in_file)

    count_rejected_per_session(sessions, rejected)
    results = [analyze_session(sessions[recording_id]) for recording_id in sorted(sessions)]

    try:
        created_files = write_reports(results, rejected, args.output)
    except DataFileError as error:
        print(f"Could not save the reports - {error}", file=sys.stderr)
        return 1

    print(f"Accepted rows: {accepted_rows}")
    print(f"Rejected rows: {len(rejected)}")
    print(f"Sessions analyzed: {len(results)}")
    print("Created files:")
    for path in created_files:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
