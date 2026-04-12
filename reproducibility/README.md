# Reproducibility

This directory contains the tracked artifacts behind the public reproducibility claim.

- `minimal/station_raw.csv` is the bundled raw reviewer fixture.
- `minimal/station_cleaned_expected.csv` is the tracked expected cleaned output.
- `minimal_second/` contains a second small raw/expected pair for broader field coverage.
- `real_provenance_example/` is the only upstream-traceable example: 20 rows from a recorded NOAA/NCEI Global Hourly source URL and the expected cleaned output.
- `REAL_PROVENANCE_EXAMPLE.md` records the source URL, retrieval date, upstream checksum observed at retrieval, row selection method, and exact cleaning command for `real_provenance_example/`.
- `checksums.sha256` is the canonical checksum manifest for tracked reproducibility artifacts.
- `station_03041099999_aonach_mor/`, `station_01116099999_stokka/`, and `station_94368099999_hamilton_island/` contain 4-row station fixtures selected from local real-station examples to broaden reviewer evidence without adding large data files.
- `FIXTURE_PROVENANCE.md` records the fixture source and selection boundary, including the fact that exact upstream retrieval dates were not retained for the curated station slices.
- `run_pipeline_example.py` is an internal/developer helper for rerunning the minimal fixture; the public reviewer workflow remains the `noaa-spec clean` CLI documented in `../REPRODUCIBILITY.md`.

The active reviewer workflow is documented in [../REPRODUCIBILITY.md](../REPRODUCIBILITY.md). Use that document for the exact commands and `checksums.sha256` for checksum targets.
The in-repo fixtures are intentionally small and serve as deterministic reproducibility checks: `clean(committed_input) = committed_output`. Only `real_provenance_example/` adds upstream URL/date/checksum traceability.
