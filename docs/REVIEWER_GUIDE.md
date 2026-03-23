# Reviewer Guide

This guide is the shortest path for evaluating NOAA-Spec in its current pre-freeze state.

## What to evaluate now

NOAA-Spec is scientific software for turning NOAA ISD / Global Hourly records into deterministic artifacts:

- canonical cleaned datasets,
- domain datasets,
- quality reports,
- release manifests with checksums and lineage.

This repository is still in active development. The final frozen submission revision and paired larger-build evidence are not being packaged in this pass.

## Install

```bash
poetry install
```

Quick smoke test:

```bash
./scripts/smoke_test_install.sh
```

## Run the sample example

```bash
python reproducibility/run_pipeline_example.py --out /tmp/noaa-spec-sample.csv
```

What this demonstrates:

- the package installs,
- the cleaning engine runs deterministically on a bounded input,
- sentinel handling, scaling, and QC-aware normalization are active,
- the same core cleaning code used by the library and CLI is exercised.

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
- checksums make those recorded artifacts auditable,
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

## How to read larger validation evidence

The repository includes active validation surfaces such as parser/spec guardrails, publication-schema tests, and documentation integrity checks. Those support day-to-day development.

Larger bounded build evidence is separate from this minimal tracked sample path. In the final submission pass, that evidence should be paired to a frozen repository revision so reviewers can evaluate one exact code-and-build snapshot together.
