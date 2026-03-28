# NOAA-Spec

## Supported Platform

The canonical reviewer workflow is containerized with Docker so it runs consistently independent of host system configuration.

An alternative local workflow is provided for advanced users on Linux with Python 3.12+ and bash.

## What NOAA-Spec does

NOAA-Spec converts raw NOAA Integrated Surface Database (ISD) / Global Hourly records into deterministic, specification-constrained cleaned outputs. In this repository snapshot, the reviewer-verifiable surface is a bounded cleaning example with checksum verification and tests.

NOAA-Spec is intended for researchers and engineers who need reproducible preprocessing of NOAA ISD / Global Hourly observations before downstream analysis.

## Why NOAA ISD is not analysis-ready

NOAA ISD observations contain fixed-width fields, comma-encoded substructures, sentinel values, quality flags, and section-dependent semantics that must be interpreted from NOAA documentation before downstream use is reproducible.

## Installation

`requirements-review.txt` is the exact tested reviewer dependency set for this revision.

`pip install -e .` installs the `noaa_spec` package from this repository checkout.

Tested in a fresh environment with no pre-installed package.

For this revision, only the Reviewer Quickstart and `reproducibility/README.md` define the supported reproducibility path.

The canonical reviewer example is under `reproducibility/minimal/`.

No archived release bundle is linked for this revision.

## System Prerequisites

The canonical reviewer path requires Docker on the host and no additional reviewer-managed OS packages inside the container.

The alternative local workflow requires host system packages including `python3`, `python3-venv`, `git`, `bash`, and `sha256sum`.

## Reviewer Quickstart (Docker)

```bash
docker build -t noaa-spec .
docker run --rm noaa-spec
```

Expected output:

- the minimal example runs
- `PASS: reproducibility verification succeeded.`
- `pytest` passes

Expected SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

This is the canonical reviewer path. It requires no OS-level dependency installation by the reviewer and no `sudo` inside the container.

## Alternative: Local Environment (Advanced Users)

This path is not the primary reviewer path. It requires host system packages including `python3`, `python3-venv`, `git`, `bash`, and `sha256sum`.

```bash
bash scripts/check_reviewer_env.sh
python3 -m venv .review-venv
source .review-venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-review.txt
pip install -e .
python reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
bash scripts/verify_reproducibility.sh
pytest -q
```

## Reproducibility Boundary

This revision demonstrates deterministic, specification-constrained cleaning at bounded scale using tracked reproducibility fixtures.

Full release-scale artifacts are not bundled as reviewer evidence in this revision.

## Contracts and Validation

NOAA-Spec is organized around explicit software surfaces:

- the canonical cleaning pipeline
- artifact contracts and schema validation
- deterministic serialization and checksum verification
- tests that guard parser behavior and documentation integrity

In the Docker reviewer path, `sha256sum` and `git` are provided inside the container. In the alternative local path, `sha256sum` is required for checksum verification and `git` is required by the test suite.

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
- JOSS paper source: [paper/paper.md](paper/paper.md)
- Docs index: [docs/README.md](docs/README.md)
