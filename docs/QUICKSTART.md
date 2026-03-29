# Quickstart

## Fastest path

From a fresh clone:

```bash
pip install -e .
python3 -m noaa_spec.quickstart
```

Expected result:

- a cleaned CSV is written to `/tmp/noaa-spec-quickstart/station_cleaned.csv`
- the command prints a small preview of the cleaned data
- the command explains one concrete transformation: `TMP=+9999,9` becomes an empty `temperature_c` value with QC code `9` preserved

## Clean your own file

Use the simplified CLI when you already have a raw NOAA CSV:

```bash
noaa-spec clean path/to/raw_station.csv --out ./output/station_cleaned.csv
```

This wraps the existing cleaner without requiring batch-run arguments or release-layout knowledge.

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
