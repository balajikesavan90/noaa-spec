# Changelog

## 1.0.0

### Core
- Deterministic canonical cleaning contract for NOAA ISD / Global Hourly observations.
- Sentinel-coded values replaced with explicit nulls; NOAA quality codes preserved in sidecar columns.
- Stable observation-level output schema with deterministic serialization and checksum-backed verification.

### CLI
- Public `noaa-spec clean` CLI for canonical CSV output.
- Optional `--view` datasets: `metadata`, `wind`, `precipitation`, `clouds_visibility`, `pressure_temperature`, `remarks`.

### Reproducibility
- Tracked minimal fixture (`reproducibility/minimal/`) with raw input, expected output, and SHA256 checksum.
- Docker-based reviewer verification path (`scripts/verify_reproducibility.sh`).

### Testing and CI
- Comprehensive test suite (1,800+ tests) covering cleaning logic, deterministic I/O, domain publishing, and contract validation.
- CI workflow for full test suite and README command validation.

### Repository
- Installable package renamed to `noaa-spec` (import as `noaa_spec`).
- Repository restructured for JOSS submission with clear public/maintainer-internal boundary.
