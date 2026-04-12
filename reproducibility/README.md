# Reproducibility

This directory contains the tracked artifacts behind NOAA-Spec's portable reproducibility checks.

- `minimal/station_raw.csv` is the bundled raw fixture.
- `minimal/station_cleaned_expected.csv` is the tracked expected canonical output.
- `run_pipeline_example.py` reruns the fixture and writes a deterministic cleaned CSV.

The active reproducibility workflow is documented in [../REPRODUCIBILITY.md](../REPRODUCIBILITY.md). Use that document for the exact commands and checksum targets.
The primary in-repo fixture is intentionally minimal and serves as a deterministic reproducibility check. Larger-scale runs are supported by broader repository infrastructure but are not bundled in this directory.
