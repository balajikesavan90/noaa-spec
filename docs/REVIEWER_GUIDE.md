# Reviewer Guide

This page defines scope. The root `README.md` contains the single canonical reviewer command sequence.

## What to evaluate now

This revision demonstrates deterministic, specification-constrained cleaning using tracked reproducibility fixtures at bounded scale. Full release-scale artifact generation is part of the broader publication workflow, but is not bundled as reviewer evidence in this revision.

No archived release bundle is linked for this revision.

## Canonical reviewer path

Run only the command sequence in the root `README.md`:

- create a fresh virtual environment
- install `requirements-review.txt`
- install the package with `pip install -e .`
- run `python reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv`
- run `bash scripts/verify_reproducibility.sh`
- run `pytest -q`

Expected SHA256 for the minimal fixture: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

## How to interpret the evidence

Reviewer-verifiable in this revision:

- editable package installation with `pip`
- the bounded cleaning example in `reproducibility/minimal/`
- deterministic checksum verification
- the test suite

Not bundled as reviewer evidence in this revision:

- archived release bundles
- frozen release manifests from a published build
- production-scale artifact runs outside the repository

## Boundary note

The repository design includes canonical cleaned outputs, domain datasets, quality reports, and release manifests. For this revision, reviewers should evaluate only the bounded reproducibility example and tests that are directly runnable from a fresh checkout.
