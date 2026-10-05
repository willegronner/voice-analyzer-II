# Podcast Voice and Recording Analyzer

Basic Python through classes - Assignment II, Option B
Wille Mikal Grønner - Student number: 7085

Reads speaker profiles and recording sessions from csv files, rejects invalid
rows, classifies each recording and saves reports in `output/`.

## How to run it

```bash
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY
python3 main.py
```

Uses the files in `data/` by default. Other files can be given with
`--profiles`, `--sessions` (one or more) and `--output`. Use `python` if your
system doesn't have `python3`. Only the standard library is used.

Tests: `python3 -m unittest discover -s tests -v`

## Structure

- `main.py` - command line and summary
- `podcast_analyzer/` - exceptions, validation, models, loader, analysis, reporting
- `tests/` - unit tests
- `data/` - the supplied csv files

## Rules

- Speaker id is `S` + three digits, recording id is `REC-YYYY-NNN`.
- Rows with missing, wrongly typed or out-of-range values, wrong number of
  fields or an unknown speaker are rejected and written to
  `output/rejected_records.txt` (row number = line in the csv, header is row 1).
- Windows without speech, and speech windows with signal quality below 0.5,
  are kept but left out of the averages.
- Fewer than 3 usable windows or under 40% usable rows gives `insufficient_data`.
- The rest is classified as in Assignment I (±12% of the speaker's usual
  values counts as similar).

## Example output

```
Accepted rows: 27
Rejected rows: 9
Sessions analyzed: 7
Created files:
  output/analysis_summary.csv
  output/analysis_report.txt
  output/rejected_records.txt
```

## Limitations

- Thresholds are tuned by trial and error on the supplied data.
- A recording where every row is rejected only shows up in `rejected_records.txt`.
