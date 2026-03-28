# Reproducibility

This directory contains the tracked bounded reproducibility fixtures used for reviewer verification.

- `minimal/` is the canonical reviewer example
- `full_station/` is an optional larger local check and is not part of reviewer verification

Tested on Linux with `Python 3.12`.

Documented prerequisites:

- `python3`
- virtual environment support for your Python installation
- Debian/Ubuntu-like systems commonly need `python3-venv`

## Canonical reviewer flow

Use the single command sequence from the root [README.md](../README.md):

```bash
python3 -m venv .review-venv
source .review-venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-review.txt
pip install -e .
python reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
bash scripts/verify_reproducibility.sh
pytest -q
```

Expected SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

`requirements-review.txt` is the reviewer dependency snapshot for this submission revision. Package metadata in `pyproject.toml` defines install requirements. `requirements-review.txt` records the exact tested reviewer environment for this revision.

These steps were designed to run in a fresh virtual environment.

Clean-room sanity check:

- do not rely on pre-existing Poetry environments
- do not rely on system packages outside the documented prerequisites

No archived release bundle is linked for this revision. Reviewers should rely on the bounded reproducibility example and test suite.

## What the verification script checks

`bash scripts/verify_reproducibility.sh`:

- imports the installed package
- runs the minimal example if needed
- computes the output checksum
- compares it against the tracked expected fixture
- fails if tracked reproducibility files were modified

Tracked anchors for the minimal example:

- `reproducibility/minimal/station_raw.csv`
- `reproducibility/minimal/station_cleaned.csv`
- `reproducibility/minimal/station_cleaned_expected.csv`

## Optional local development path

Developer workflow only. Not part of reviewer quickstart.

```bash
python reproducibility/run_pipeline_example.py --example full_station --out /tmp/noaa-spec-full-station.csv
```

If you use Poetry for local development, treat it as developer workflow only. It is not part of the reviewer path.
