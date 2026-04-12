# Reproducibility

This directory contains the tracked artifacts behind the public reproducibility claim.

- `minimal/station_raw.csv` is the bundled raw reviewer fixture.
- `minimal/station_cleaned_expected.csv` is the tracked expected cleaned output.
- `minimal_second/` contains a second small raw/expected pair for broader field coverage.
- `station_03041099999_aonach_mor/`, `station_01116099999_stokka/`, and `station_94368099999_hamilton_island/` contain 4-row station fixtures selected from local real-station examples to broaden reviewer evidence without adding large data files.
- `run_pipeline_example.py` is an internal/developer helper for rerunning the minimal fixture; the public reviewer workflow remains the `noaa-spec clean` CLI documented in `../REPRODUCIBILITY.md`.

The active reviewer workflow is documented in [../REPRODUCIBILITY.md](../REPRODUCIBILITY.md). Use that document for the exact commands and checksum target.
The in-repo fixtures are intentionally small and serve as deterministic reproducibility checks.
