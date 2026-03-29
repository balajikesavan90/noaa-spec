# Quickstart

## Fastest path

User quickstart for Python 3.12+ from a fresh clone:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
python3 -m noaa_spec.quickstart
```

Expected result:

- a cleaned CSV is written to `/tmp/noaa-spec-quickstart/station_cleaned.csv`
- the command prints a small preview of the cleaned data
- the command explains one concrete transformation: `TMP=+9999,9` becomes a missing `temperature_c` value (`NaN`) with QC code `9` preserved

This is the primary path for ordinary users. If `python3 -m venv .venv` fails on your system, use `bash scripts/check_reviewer_env.sh` as an optional troubleshooting helper. Reviewer reproducibility checks are separate and live in [../reproducibility/README.md](../reproducibility/README.md).

## Clean your own file

Use the simplified CLI when you already have a raw NOAA CSV:

```bash
noaa-spec clean my_station.csv --out cleaned.csv
```

`my_station.csv` should be a raw NOAA ISD / Global Hourly CSV in the same general structure as the bundled sample. You can inspect the bundled sample at `reproducibility/minimal/station_raw.csv` for reference.

Most ordinary users only need the `clean` command. Other commands support batch, publication, or maintainer workflows and are not needed for a first successful run.

## Output interpretation

After the quickstart or `clean` command, go to [UNDERSTANDING_OUTPUT.md](UNDERSTANDING_OUTPUT.md) for the cleaned-column subset, sentinel examples, and QC field explanation.

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

- Reproducibility and reviewer path: [../reproducibility/README.md](../reproducibility/README.md)
- Output interpretation: [UNDERSTANDING_OUTPUT.md](UNDERSTANDING_OUTPUT.md)
- Example files and station snapshots: [examples/README.md](examples/README.md)
- Internal maintainer docs: [internal/README.md](internal/README.md)
