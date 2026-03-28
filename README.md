# NOAA-Spec

## What NOAA-Spec does

NOAA-Spec converts raw NOAA Integrated Surface Database (ISD) / Global Hourly records into deterministic, specification-constrained cleaned outputs. In this repository snapshot, the reviewer-verifiable surface is a bounded cleaning example with checksum verification and tests.

NOAA-Spec is intended for researchers and engineers who need reproducible preprocessing of NOAA ISD / Global Hourly observations before downstream analysis.

## Why NOAA ISD is not analysis-ready

NOAA ISD observations contain fixed-width fields, comma-encoded substructures, sentinel values, quality flags, and section-dependent semantics that must be interpreted from NOAA documentation before downstream use is reproducible.

## Installation

Tested on Linux with `Python 3.12`.

Documented prerequisites:

- `python3`
- virtual environment support for your Python installation
- Debian/Ubuntu-like systems commonly need `python3-venv`

These steps were designed to run in a fresh virtual environment.

Clean-room sanity check:

- do not rely on pre-existing Poetry environments
- do not rely on system packages outside the documented prerequisites

`requirements-review.txt` is the reviewer dependency snapshot for this submission revision. Package metadata in `pyproject.toml` defines the install requirements. `requirements-review.txt` captures the exact tested reviewer environment for this revision.

Poetry may still be used for developer workflow only. It is not part of the reviewer quickstart.

## Reviewer Quickstart

```bash
python3 -m venv .review-venv
source .review-venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-review.txt
pip install -e .
python reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
bash scripts/verify_reproducibility.sh
pytest -q
```

Expected SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

`scripts/check_reviewer_env.sh` provides a lightweight sanity check for the active reviewer environment.

## Supported Reviewer Commands

These are the reviewer commands for this repository snapshot:

```bash
python reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
bash scripts/verify_reproducibility.sh
pytest -q
```

Success means:

- the minimal example writes `/tmp/noaa-spec-sample.csv`
- `bash scripts/verify_reproducibility.sh` prints `PASS:` and the expected SHA256
- `pytest -q` completes in the active virtual environment

## Reproducibility Boundary

This revision demonstrates deterministic, specification-constrained cleaning using tracked reproducibility fixtures at bounded scale. Full release-scale artifact generation is part of the broader publication workflow, but is not bundled as reviewer evidence in this revision.

No archived release bundle is linked for this revision. Reviewers should rely on the bounded reproducibility example and test suite.

## Contracts and Validation

NOAA-Spec is organized around explicit software surfaces:

- the canonical cleaning pipeline,
- artifact contracts and schema validation,
- deterministic serialization and checksum verification,
- tests that guard parser behavior and documentation integrity.

The broader release-oriented publication workflow remains part of the repository design, but the reviewer-facing evidence in this revision is the bounded reproducibility example plus the test suite.

## When to use / when not to use

Use NOAA-Spec when you need:

- deterministic preprocessing of NOAA ISD / Global Hourly data
- explicit handling of sentinel and quality semantics
- a reproducible cleaning surface that can be verified with fixtures and tests

Do not use NOAA-Spec when you need:

- downstream climate analysis or modeling workflows
- a generic ETL framework for unrelated datasets
- proof of full archived release outputs from this repository snapshot

## Paper and docs links

- Reviewer guide: [docs/REVIEWER_GUIDE.md](docs/REVIEWER_GUIDE.md)
- Reproducibility notes: [reproducibility/README.md](reproducibility/README.md)
- Example scripts: [examples/README.md](examples/README.md)
- JOSS paper source: [paper/paper.md](paper/paper.md)
- Docs index: [docs/README.md](docs/README.md)
