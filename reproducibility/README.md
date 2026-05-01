# Reproducibility

This directory contains the tracked artifacts behind the public reproducibility claim.

- `minimal/station_raw.csv` is the bundled raw reproducibility fixture.
- `minimal/station_cleaned_expected.csv` is the tracked expected cleaned output.
- `minimal_second/` contains a second small raw/expected pair for broader field coverage.
- `real_provenance_example/` is an upstream-traceable 20-row source slice from a recorded NOAA/NCEI Global Hourly source URL and the expected cleaned output.
- `traceable_peru_il_2014_aa1_qc/` and `traceable_albion_ne_2014_calm_aa1/` are one-row upstream-traceable source slices promoted from documented edge cases.
- `TRACEABLE_FIXTURES.md` records source URLs, retrieval dates, upstream checksums observed at retrieval, row selection methods, and exact extraction/cleaning commands for the traceable fixtures.
- `checksums.sha256` is the canonical checksum manifest for tracked reproducibility artifacts.
- `station_03041099999_aonach_mor/`, `station_01116099999_stokka/`, and `station_94368099999_hamilton_island/` contain 4-row committed station fixtures that broaden deterministic input/output checks without adding large data files.
- `FIXTURE_PROVENANCE.md` records the fixture source and selection boundary, including the fact that exact upstream retrieval dates were not retained for the curated station slices.
- `run_pipeline_example.py` is a maintainer helper for rerunning the minimal fixture; the public workflow reproducibility path remains the `noaa-spec clean` CLI documented in `../REPRODUCIBILITY.md`.

The active reproducibility workflow is documented in [../REPRODUCIBILITY.md](../REPRODUCIBILITY.md). Use that document for the exact commands and `checksums.sha256` for checksum targets.
The in-repo fixtures are intentionally small and serve as deterministic reproducibility checks: `clean(committed_input) = committed_output`. The three traceable fixture directories add upstream URL/date/checksum traceability; the older curated station fixtures do not replay upstream acquisition.
For the claim-to-evidence boundary, see [../docs/evidence_matrix.md](../docs/evidence_matrix.md).
