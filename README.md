# NOAA-Spec

## What this does

NOAA-Spec is a reusable NOAA-specific cleaner for NOAA Integrated Surface Database (ISD) / Global Hourly observation records. It turns raw encoded rows into this package's canonical cleaned representation: deterministic observation-level output with explicit handling of sentinels, quality-code semantics, and stable column names. It is for researchers and engineers who want one inspectable cleaning surface instead of rebuilding NOAA-specific parsing logic in project-local scripts.

## 2-minute quickstart

User quickstart for Python 3.12+:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
python3 -m noaa_spec.quickstart
```

This writes a cleaned sample CSV to:

```text
/tmp/noaa-spec-quickstart/station_cleaned.csv
```

This is the primary ordinary-user path. If `python3 -m venv .venv` fails because `venv` support is missing on your system, use the optional helper `bash scripts/check_reviewer_env.sh` to diagnose missing OS packages. Reviewer and maintainer workflows are separate and documented below.

## Use this on your own NOAA data

After the bundled sample runs, clean a user-owned NOAA file:

```bash
noaa-spec clean my_station.csv --out cleaned.csv
```

`my_station.csv` should be a raw NOAA ISD / Global Hourly CSV in the same general structure as the bundled sample. For reference, inspect the bundled sample at [reproducibility/minimal/station_raw.csv](reproducibility/minimal/station_raw.csv).

Most ordinary users only need the `clean` command. The other CLI commands support batch, pipeline, or advanced workflows.

## Reproducibility boundary

Reviewer-verifiable from this repository alone:

- the canonical cleaning command exposed through `noaa-spec clean ...`
- the bundled quickstart sample
- the tracked reproducibility fixture in `reproducibility/minimal/`
- checksum-backed verification through [reproducibility/README.md](reproducibility/README.md)

Included in the repository but not part of the bounded JOSS review surface:

- broader release/publication layout under [release/README.md](release/README.md)
- domain-split, reporting, and operations material under [docs/internal/README.md](docs/internal/README.md)
- curated illustrative example artifacts under [docs/examples/README.md](docs/examples/README.md)

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

- sentinel values such as `+9999,9` become missing values (`NaN`) instead of fake numbers
- QC codes are preserved in separate columns instead of being discarded
- numeric weather fields are normalized into consistent units and column names
- the output is written deterministically so reruns produce the same artifact

Start by reading the measurement columns such as `temperature_c`, `dew_point_c`, `wind_speed_ms`, and `visibility_m`. Many `*_QC` and `__qc_*` columns can be ignored at first unless you need quality-based filtering or want to inspect why a cleaned value is missing (`NaN`). A fuller explanation is in [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md).

## Reviewer reproducibility

Use this only for bounded review or reproducibility checks. It is intentionally separate from the ordinary-user quickstart above.

Run from a clean checkout so the result does not depend on an existing editable install or active virtual environment.

Build the reviewer image from the repository root:

```bash
docker build -f Dockerfile -t noaa-spec-review .
```

Run the bounded reproducibility check inside the container:

```bash
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

For the complete reviewer workflow, expected artifacts, and optional local debugging path, see [reproducibility/README.md](reproducibility/README.md).

## When to use this

Use NOAA-Spec when you need deterministic NOAA cleaning, explicit QC handling, and a stable cleaned observation-level dataset you can compare or reuse across downstream work.

## Why not just use pandas?

- raw NOAA fields embed sentinel values and subfield encodings that are easy to handle inconsistently
- QC semantics vary by field, and this package keeps them aligned with the cleaned values
- using one documented cleaning surface reduces station-to-station drift in downstream work
- deterministic output writing helps reviewers and downstream users confirm that the cleaning path has not drifted

This is overkill when you only need a quick one-off exploration of a tiny sample, are comfortable interpreting NOAA encoded fields yourself, or do not care about preserving QC context.

## Full docs

- Quickstart details: [docs/QUICKSTART.md](docs/QUICKSTART.md)
- Understand the output: [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md)
- Reproducibility guide: [reproducibility/README.md](reproducibility/README.md)
- Examples: [docs/examples/README.md](docs/examples/README.md)
- Minimal example script: [examples/run_minimal_cleaning.py](examples/run_minimal_cleaning.py)
- Internal maintainer docs for broader publication and operations workflows: [docs/internal/README.md](docs/internal/README.md)
