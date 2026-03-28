# NOAA-Spec

## Supported Platform

The canonical reviewer workflow is containerized with Docker so it runs consistently independent of host system configuration.

An alternative local workflow is provided for advanced users on Linux with Python 3.12+ and bash.

The supported reviewer path for this submission is Docker. Local installation is optional and intended for development only; it is not required for reproducibility validation.

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

Optional local development instructions are in [docs/LOCAL_DEV.md](docs/LOCAL_DEV.md).

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
- `2194 passed, 15 skipped`

Expected SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

This is the canonical reviewer path. It requires no OS-level dependency installation by the reviewer and no `sudo` inside the container.

Local installation is optional and intended for development only. Reviewer-facing reproducibility validation should use the Docker workflow above.

## Reproducibility Boundary

This submission validates deterministic canonical cleaning using a bounded, checksum-verified example included in-repo. Broader publication artifacts (release bundles, manifests, and quality reports) are part of the system design but are not included in this review package.

## Contracts and Validation

NOAA-Spec is organized around explicit software surfaces:

- the canonical cleaning pipeline
- artifact contracts and schema validation
- deterministic serialization and checksum verification
- tests that guard parser behavior and documentation integrity

In the Docker reviewer path, `sha256sum` and `git` are provided inside the container.

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
