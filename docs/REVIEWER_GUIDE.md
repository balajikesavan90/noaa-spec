# Reviewer Guide

This guide is the shortest path for evaluating NOAA-Spec from a clean checkout. The root `README.md` is the canonical reviewer path; this page mirrors it in a tighter audit-oriented format.

## What to evaluate now

This repository snapshot demonstrates the canonical cleaning pipeline and deterministic output generation on a tracked sample input. Full release-scale artifacts are not included in this development snapshot.

## Install

Tested on clean Linux (`Python 3.12`, `PEP 668`).

Primary path:

```bash
python3 --version
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
poetry install
```

Fallback path:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install poetry
poetry install
```

This project relies on `poetry.lock` for deterministic dependency resolution. Do not regenerate it unless you are intentionally updating dependencies.

## Reviewer Quickstart (3 Steps)

1. Install the project with one of the two paths above.

2. Run the bounded deterministic example:

```bash
poetry run python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
```

3. Verify the installed output:

```bash
bash scripts/verify_reproducibility.sh
```

Manual verification:

```bash
poetry run noaa-spec --help
sha256sum /tmp/noaa-spec-sample.csv
sha256sum reproducibility/minimal/station_cleaned_expected.csv
```

Expected SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

What this demonstrates:

- the package installs on a clean Linux environment without relying on `pipx`
- the cleaning engine runs deterministically on a bounded input
- the documented CLI is available without a global install
- the generated CSV matches the tracked expected artifact byte-for-byte

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

- frozen post-freeze release artifacts
- production-scale archived outputs

The repository includes active validation surfaces such as parser/spec guardrails, publication-schema tests, and documentation integrity checks. Those support day-to-day development.

Larger bounded build evidence is separate from this minimal tracked sample path. In the final submission pass, that evidence should be paired to a frozen repository revision so reviewers can evaluate one exact code-and-build snapshot together.
