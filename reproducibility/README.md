# Reproducibility

This directory contains the tracked artifacts behind the public reproducibility claim.

- `minimal/station_raw.csv` is the bundled raw reviewer fixture.
- `minimal/station_cleaned_expected.csv` is the tracked expected canonical output.
- `run_pipeline_example.py` reruns the fixture and writes a deterministic cleaned CSV.

The active reviewer workflow is documented in [../REPRODUCIBILITY.md](../REPRODUCIBILITY.md). Use that document for the exact commands and checksum target.
The in-repo fixture is intentionally minimal and serves as a deterministic reproducibility proof. Larger-scale runs are supported but not bundled in this directory.
