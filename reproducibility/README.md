# Reproducibility

This directory contains the tracked artifacts behind the public reproducibility claim.

- `minimal/station_raw.csv` is the bundled raw reviewer fixture.
- `minimal/station_cleaned_expected.csv` is the tracked expected canonical output.
- `run_pipeline_example.py` reruns the fixture and writes a deterministic cleaned CSV.
- `full_station/` contains the larger tracked example used by tests.

For reviewer use, the active workflow is:

1. build the review container,
2. run `bash scripts/verify_reproducibility.sh`,
3. inspect `minimal/station_cleaned_expected.csv` if you want a stable canonical sample without rerunning anything else.

Use [../REPRODUCIBILITY.md](../REPRODUCIBILITY.md) for the exact commands and checksum target.
