# NOAA-Spec

## What this does

NOAA-Spec cleans NOAA Integrated Surface Database (ISD) / Global Hourly records into a stable, structured canonical dataset for downstream analysis. It is for researchers and engineers who want NOAA-specific cleaning rules handled consistently instead of rebuilding them in notebooks. The package exists to make sentinel handling, quality-code preservation, and output reproducibility explicit.

## 2-minute quickstart

User quickstart for Python 3.12+:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python3 -m noaa_spec.quickstart
```

This writes a cleaned sample CSV to:

```text
/tmp/noaa-spec-quickstart/station_cleaned.csv
```

This is the ordinary user path. Use Poetry for development workflows. Use Docker for the reviewer/reproducibility workflow.

## Which path should I use?

Quickstart for users:

- local virtual environment
- `pip install -e .`
- `python3 -m noaa_spec.quickstart`

Development:

- Poetry
- see [docs/internal/LOCAL_DEV.md](docs/internal/LOCAL_DEV.md)

Reproducibility / review:

- Docker
- see [reproducibility/README.md](reproducibility/README.md)

## Use this on your own NOAA data

After the bundled sample runs, clean a user-owned NOAA file:

```bash
noaa-spec clean my_station.csv --out cleaned.csv
```

`my_station.csv` should be a raw NOAA ISD / Global Hourly CSV in the same general structure as the bundled sample. For reference, inspect the bundled sample at [`reproducibility/minimal/station_raw.csv`](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/reproducibility/minimal/station_raw.csv).

## One realistic local workflow

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python3 -m noaa_spec.quickstart
noaa-spec clean my_station.csv --out cleaned.csv
```

## What you get

Small before vs after example:

```text
Before: TMP="+9999,9", DEW="+9999,9", VIS="999999,9,N,1"
After:  temperature_c=, temperature_quality_code=9, dew_point_c=, visibility_m=
```

The cleaned output keeps NOAA context while making core values usable:

- `STATION`: NOAA station identifier.
- `DATE`: observation timestamp from the source row.
- `temperature_c`: cleaned Celsius temperature.
- `temperature_quality_code`: original NOAA QC code for temperature.
- `wind_speed_ms`: cleaned wind speed in meters per second.

What changed:

- sentinel values such as `+9999,9` become empty values instead of fake numbers
- QC codes are preserved in separate columns instead of being discarded
- numeric weather fields are normalized into consistent units and column names
- the output is written deterministically so reruns produce the same artifact

Start by reading the measurement columns such as `temperature_c`, `dew_point_c`, `wind_speed_ms`, and `visibility_m`. Many `*_QC` and `__qc_*` columns can be ignored at first unless you need quality-based filtering or want to inspect why a cleaned value is empty. A fuller explanation is in [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md).

## When to use this

Use NOAA-Spec when you need repeatable NOAA cleaning across stations, explicit QC handling, and a stable cleaned dataset you can cite, compare, or reuse.

## Why not just use pandas?

- raw NOAA fields embed sentinel values and subfield encodings that are easy to handle inconsistently
- QC semantics vary by field, and this package keeps them aligned with the cleaned values
- using one documented cleaning surface reduces station-to-station drift in downstream work
- deterministic output writing helps with reproducibility and release workflows

This is overkill when you only need a quick one-off exploration of a tiny sample, are comfortable interpreting NOAA encoded fields yourself, or do not care about preserving QC context.

## Full docs

- Quickstart details: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- Understand the output: [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md)
- Examples: [docs/examples/README.md](docs/examples/README.md)
- Minimal example script: [examples/run_minimal_cleaning.py](examples/run_minimal_cleaning.py)
- Reproducibility notes: [reproducibility/README.md](reproducibility/README.md)
- Internal architecture, reviewer, validation, and operations docs: [docs/internal/README.md](docs/internal/README.md)
