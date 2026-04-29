# Changelog

## 1.0.0

### Core
- Implemented deterministic cleaned CSV output for NOAA ISD / Global Hourly observation rows handled by `noaa-spec clean`.
- Normalized documented sentinel-coded measurements to null cells while preserving NOAA quality codes in explicit output columns.
- Kept the public output observation-level and checksum-stable through deterministic row ordering and CSV serialization.
- Defined the JOSS-facing scope as cleaning only: no downloader, release builder, orchestration layer, domain dataset publishing system, or analysis workflow.

### CLI
- Added the public invocation `noaa-spec clean INPUT.csv OUTPUT.csv`.
- Kept `--out OUTPUT.csv` as a legacy alternate output-path form.

### Reproducibility
- Added committed raw/expected fixture pairs under `reproducibility/` with SHA256 checksums for regenerated cleaned outputs.
- Added `reproducibility/real_provenance_example/` with one recorded NOAA/NCEI source URL, retrieval date, upstream checksum, raw slice, and expected cleaned output.
- Added Docker-based reproducibility verification through `scripts/verify_reproducibility.sh` and the pinned Docker verification dependency file `requirements-review.txt`.

### Testing and CI
- Added focused tests for cleaning logic, sentinel/QC handling, deterministic I/O, CLI behavior, and fixture reproduction.
- Added CI coverage for the focused test suite and checksum reproducibility verification.

### Repository
- Installable package renamed to `noaa-spec` (import as `noaa_spec`).
- JOSS branch narrowed around the cleaning package, reproducibility fixtures, tests, and manuscript rather than broader publication workflows.
- Documented the evidence boundary between tracked fixture reproduction, three upstream-traceable fixtures, compact edge-case examples, and broader unit-tested parser behavior.
