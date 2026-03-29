# Quickstart

## Fastest path

User quickstart for Python 3.12+ from a fresh clone:

```bash
bash scripts/check_reviewer_env.sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python3 -m noaa_spec.quickstart
```

Run `bash scripts/check_reviewer_env.sh` first to confirm your local Python installation includes the required `venv` support. If `venv` support is missing, install `python3-venv` with your system package manager and rerun the check.

Expected result:

- a cleaned CSV is written to `/tmp/noaa-spec-quickstart/station_cleaned.csv`
- the command prints a small preview of the cleaned data
- the command explains one concrete transformation: `TMP=+9999,9` becomes a missing `temperature_c` value (`NaN`) with QC code `9` preserved

Use Poetry for development workflows. Use Docker for reviewer reproducibility checks.

## Clean your own file

Use the simplified CLI when you already have a raw NOAA CSV:

```bash
noaa-spec clean my_station.csv --out cleaned.csv
```

`my_station.csv` should be a raw NOAA ISD / Global Hourly CSV in the same general structure as the bundled sample. You can inspect the bundled sample at `reproducibility/minimal/station_raw.csv` for reference.

Most ordinary users only need the `clean` command. The other commands support batch, pipeline, or advanced workflows.

## One realistic local workflow

```bash
bash scripts/check_reviewer_env.sh
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python3 -m noaa_spec.quickstart
noaa-spec clean my_station.csv --out cleaned.csv
```

This bridges the bundled sample to a user-owned raw NOAA file without requiring batch-run arguments or release-layout knowledge.

## Run the example script

The repository also includes a plain example script:

```bash
python3 examples/run_minimal_cleaning.py --out /tmp/noaa-spec-example.csv
```

Expected output file:

```text
/tmp/noaa-spec-example.csv
```

The script loads the bundled minimal sample, runs the cleaner, writes a deterministic CSV, and prints a short preview.

## Next docs

- Output interpretation: [UNDERSTANDING_OUTPUT.md](UNDERSTANDING_OUTPUT.md)
- Example files and station snapshots: [examples/README.md](examples/README.md)
- Internal and reviewer docs: [internal/README.md](internal/README.md)
