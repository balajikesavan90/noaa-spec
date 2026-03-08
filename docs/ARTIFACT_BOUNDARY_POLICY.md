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

## Runtime Artifact Surface (Not Publication)

The following locations are runtime/operational surfaces and are not the publication contract:

- `output/`
- `artifacts/test_runs/`
- `artifacts/parquet_runs/`

These paths are for local processing, debugging, or transient operational records.

## Fixture and Example Surface

Tracked examples and fixtures must live outside runtime roots:

- docs examples: `docs/examples/`
- test fixtures: `tests/fixtures/`

Tracked station report examples are stored at:

- `docs/examples/station_reports/`
- `docs/examples/noaa_demo/`

This separation keeps publication boundaries explicit and prevents runtime state from being mistaken for release artifacts.
