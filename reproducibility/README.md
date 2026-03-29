# Reproducibility

This directory contains the tracked artifacts behind the public reproducibility claim.

- `minimal/station_raw.csv` is the bundled raw reviewer fixture.
- `minimal/station_cleaned_expected.csv` is the tracked expected canonical output.
- `run_pipeline_example.py` reruns the fixture and writes a deterministic cleaned CSV.
- `full_station/` contains the larger tracked example used by tests.

For the exact reviewer workflow, checksum target, and Docker clean-room verification, use [../REPRODUCIBILITY.md](../REPRODUCIBILITY.md).
