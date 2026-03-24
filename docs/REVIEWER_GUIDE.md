# Reviewer Guide

This guide is the shortest path for evaluating NOAA-Spec from a clean checkout.

## What to evaluate now

NOAA-Spec is scientific software for turning NOAA ISD / Global Hourly records into deterministic artifacts:

- canonical cleaned datasets,
- domain datasets,
- quality reports,
- release manifests with checksums and lineage.

This repository is still in active development. The final frozen submission revision and paired larger-build evidence are not packaged in this cleanup pass.

## Install

```bash
python3 --version
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install poetry
poetry install
```

Requirements:

- Python `>=3.12`
- `pipx` used to install Poetry on a clean machine
- Poetry available on `PATH`

Recommended Poetry installation path:

- install Poetry with `pipx`
- if `pipx` is already installed, run `pipx install poetry`
- the official Poetry installer is a viable fallback, but the reviewer path in this repository uses `pipx`

Quick smoke test:

```bash
bash scripts/smoke_test_install.sh
```

## Run the sample example

1. Run the bounded deterministic example:

```bash
poetry run python reproducibility/run_pipeline_example.py --out /tmp/noaa-spec-sample.csv
```

2. Verify the installed CLI surface:

```bash
poetry run noaa-spec --help
```

What this demonstrates:

- the package installs,
- the cleaning engine runs deterministically on a bounded input,
- the documented CLI is available without a global install,
- sentinel handling, scaling, and QC-aware normalization are active,
- the same core cleaning code used by the library and CLI is exercised.

Expected output:

- `/tmp/noaa-spec-sample.csv` exists and contains cleaned observation rows
- the sample command exits cleanly without `[PARSE_STRICT]` warnings
- `poetry run noaa-spec --help` exits successfully
- `bash scripts/smoke_test_install.sh` verifies the generated CSV against the tracked reproducibility anchor and confirms that no tracked repository file is modified by the reviewer flow

This sample run is intentionally small. It demonstrates the software interface and output semantics, not the full bounded batch evidence used for later submission packaging.

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
- `docs/CLEANING_RUN_MODES.md`
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

- `poetry install`
- the bounded example in `reproducibility/`
- the tracked tests and validation docs

External to this repository:

- large release builds
- machine-local archives
- archived operational snapshots

The repository includes active validation surfaces such as parser/spec guardrails, publication-schema tests, and documentation integrity checks. Those support day-to-day development.

Larger bounded build evidence is separate from this minimal tracked sample path. In the final submission pass, that evidence should be paired to a frozen repository revision so reviewers can evaluate one exact code-and-build snapshot together.
