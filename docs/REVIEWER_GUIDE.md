# Reviewer Guide

This page provides submission framing only. The root `README.md` contains the single canonical reviewer command sequence.

## What to evaluate now

This revision demonstrates deterministic, specification-constrained cleaning at bounded scale using tracked reproducibility fixtures. Full release-scale artifacts are part of the broader publication workflow but are not bundled as reviewer evidence in this development snapshot.

Tested on Linux with `Python 3.12`.

The repository relies on `poetry.lock` for deterministic dependency resolution.

No archived release bundle is linked for this revision.

## Canonical reviewer path

Run only the command sequence in the root `README.md`:

- install Poetry with the official installer
- run `poetry install`
- run `poetry run noaa-spec --help`
- run `poetry run python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv`
- run `bash scripts/verify_reproducibility.sh`
- run `poetry run pytest -q`

Expected SHA256 for the minimal fixture: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

## How to interpret outputs

The sample CSV shows cleaned observation rows. In larger release-oriented runs, the public artifact structure is:

```text
release/
  build_<build_id>/
    canonical_cleaned/
    domains/
    quality_reports/
    manifests/
```

Plain-language meaning:

- `canonical_cleaned/`: the full cleaned observation-level dataset.
- `domains/`: narrower, joinable datasets such as wind or precipitation.
- `quality_reports/`: descriptive evidence about completeness, sentinel frequency, QC exclusions, and usability.
- `manifests/`: release bookkeeping for checksums, schema versions, row counts, and lineage.

## Contracts, manifests, and checksums

Reviewer-facing interpretation:

- contracts define what each artifact type must contain,
- manifests record what was produced,
- publication manifests use portable relative artifact paths and content-only checksums,
- checksums make those recorded artifacts auditable across machines when artifact bytes match,
- lineage fields show how outputs relate back to raw inputs and intermediate artifacts.

Useful companion docs:

- `docs/ARTIFACT_BOUNDARY_POLICY.md`
- `docs/DOMAIN_DATASET_REGISTRY.md`

## Why a domain artifact may be absent

Not every station must emit every domain dataset.

A domain artifact may be intentionally omitted when:

- the station has no fields for that domain in the cleaned canonical data,
- all rows are invalid for that domain after cleaning and QC handling,
- no rows survive the domain projection.

This is expected behavior for sparse domains such as precipitation and should not be interpreted as a packaging failure by itself.

## Artifact boundary

Reproducible from this repository:

- the Poetry-based install path in the root `README.md`
- the bounded example in `reproducibility/`
- the tracked tests and validation docs

External to this repository:

- frozen release bundles
- production-scale archived outputs

The repository includes active validation surfaces such as parser/spec guardrails, publication-schema tests, and documentation integrity checks. Those support day-to-day development.
