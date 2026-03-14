# Artifact Boundary Policy

This repository distinguishes publication artifacts from runtime artifacts.

## Canonical Publication Surface

Release artifacts must be written under:

`release/build_<build_id>/`

Required sibling directories:

- `canonical_cleaned/`
- `domains/`
- `quality_reports/`
- `manifests/`

## Manifest Model

The build emits two manifest surfaces under `release/build_<build_id>/manifests/`:

- `release_manifest.csv`: publication manifest covering canonical lineage artifacts (`raw_source`, `canonical_dataset`, `domain_dataset`, `quality_report`).
- `file_manifest.csv`: full-file manifest covering all produced run files, including station split manifests, station reports, station quality profiles, and station `_SUCCESS.json` markers.

This dual-manifest model keeps publication lineage contracts stable while still providing complete run-file observability.

## Checksum Policy

Artifact checksums use a deterministic SHA-256 bundle hash with this exact policy:

1. append the artifact absolute path bytes
2. append a `\0` separator
3. append full file content bytes
4. append a trailing `\0`

This is a path+content policy (not content-only) and applies to both `release_manifest.csv` and `file_manifest.csv`.

## Runtime Artifact Surface (Not Publication)

The following locations are runtime/operational surfaces and are not the publication contract:

- `output/`
- `artifacts/test_runs/`
- `artifacts/parquet_runs/`
- `noaa_file_index/`
- `noaa_file_index/state/`

These paths are for local processing, debugging, or transient operational records.

## Fixture and Example Surface

Tracked examples and fixtures must live outside runtime roots:

- docs examples: `docs/examples/`
- test fixtures: `tests/fixtures/`

Tracked station report examples are stored at:

- `docs/examples/station_reports/`
- `docs/examples/noaa_demo/`

This separation keeps publication boundaries explicit and prevents runtime state from being mistaken for release artifacts.

## Tracking Policy (`.gitignore`)

Repository tracking defaults:

- CSV/Parquet runtime outputs are ignored globally.
- Runtime roots (`output/`, `artifacts/test_runs/`, `artifacts/parquet_runs/`) are ignored.

Release exception policy:

- CSV/Parquet artifacts under `release/build_*/{canonical_cleaned,domains,quality_reports,manifests}/` are explicitly unignored and may be versioned when needed for deterministic publication snapshots.
