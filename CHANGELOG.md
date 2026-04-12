# Changelog

## 1.0.0

### Core
- Deterministic cleaned-output contract for NOAA ISD / Global Hourly observations.
- Sentinel-coded values replaced with explicit nulls; NOAA quality codes preserved in sidecar columns.
- Stable observation-level output schema with deterministic serialization and checksum-backed verification.

### CLI
- Public `noaa-spec clean` CLI for deterministic cleaned CSV output.

### Reproducibility
- Tracked minimal fixture (`reproducibility/minimal/`) with raw input, expected output, and SHA256 checksum.
- Tracked secondary fixture (`reproducibility/minimal_second/`) covering additional field structures.
- Docker-based reviewer verification path (`scripts/verify_reproducibility.sh`).

### Testing and CI
- Focused JOSS test suite covering cleaning logic, QC handling, deterministic I/O, CLI behavior, and fixture reproduction.
- CI workflow for the focused test suite and reproducibility verification.

### Repository
- Installable package renamed to `noaa-spec` (import as `noaa_spec`).
- JOSS branch narrowed to the cleaning package, reproducibility fixtures, tests, and manuscript.
