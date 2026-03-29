# NOAA-Spec

## Supported Platform

The canonical reviewer workflow is containerized with Docker so it runs consistently independent of host system configuration.

An alternative local workflow is provided for advanced users on Linux with Python 3.12+ and bash.

The supported reviewer path for this submission is Docker. Local installation is optional and intended for development only; it is not required for reproducibility validation.

## What NOAA-Spec does

NOAA-Spec is a reusable NOAA-specific preprocessing package for NOAA Integrated Surface Database (ISD) / Global Hourly records. It converts encoded observations into stable cleaned outputs with explicit handling of field semantics, sentinel values, quality codes, provenance, and bounded reproducibility. Its practical purpose is to replace project-local ISD cleaning logic with one inspectable preprocessing surface so analysts using the same raw NOAA input are less likely to produce silently different cleaned datasets. In this repository snapshot, the reviewer-verifiable surface is the canonical cleaning example in `reproducibility/`, plus checksum verification and tests.

NOAA-Spec is intended for researchers and engineers who need reproducible preprocessing of NOAA ISD / Global Hourly observations before downstream analysis.

## Why NOAA ISD is not analysis-ready

NOAA ISD observations contain fixed-width fields, comma-encoded substructures, sentinel values, quality flags, and section-dependent semantics that must be interpreted from NOAA documentation before downstream use is reproducible.

## Current practice vs NOAA-Spec

Many NOAA ISD workflows rely on project-specific scripts or notebook preprocessing to interpret encoded fields, remove sentinels, and decide how quality flags affect usable values. That approach can work for one study, but it often leaves the preprocessing contract implicit and can produce silently different cleaned outputs from the same raw records.

NOAA-Spec packages those NOAA-specific steps into an inspectable software surface with deterministic cleaned outputs, explicit contracts, preserved provenance, and bounded reproducibility fixtures. A concrete committed repository example is station `16754399999` (KARPATHOS, GR): its tracked quality report records sentinel replacements for `temperature_c`, and its tracked aggregation report records separate canonical temperature-quality/status fields. NOAA-Spec makes that handling explicit instead of leaving it implicit in local script logic. The goal is a stable NOAA-specific preprocessing handoff for downstream analysis, not a generic validation framework.

## Installation

`requirements-review.txt` is the exact tested reviewer dependency set for this revision.

`pip install -e .` installs the `noaa_spec` package from this repository checkout.

Tested in a fresh environment with no pre-installed package.

For this revision, only the Reviewer Quickstart and `reproducibility/README.md` define the supported reproducibility path.

The supported reviewer path requires a working Docker installation with daemon access; the `docker` CLI alone is not sufficient.

The canonical reviewer example is under `reproducibility/minimal/`.

No archived release bundle is linked for this revision.

Optional local development instructions are in [docs/LOCAL_DEV.md](docs/LOCAL_DEV.md).

## System Prerequisites

The canonical reviewer path requires Docker on the host and no additional reviewer-managed OS packages inside the container.

The alternative local workflow requires host system packages including `python3`, `python3-venv`, `git`, `bash`, and `sha256sum`.

## Reviewer Quickstart (Docker)

This supported reviewer path requires a working Docker installation with daemon access.

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

This submission validates the bounded, checksum-backed canonical cleaning example included in-repo. Release manifests, domain publication outputs, and quality reports are part of the broader documented system design, but they are not included as reviewer-verifiable artifacts in this submission.

## Contracts and Validation

NOAA-Spec is organized around explicit software surfaces:

- the canonical cleaning pipeline
- artifact contracts and schema validation
- deterministic serialization and checksum verification
- tests that guard parser behavior and documentation integrity

These are means to user-facing ends: reproducible cleaned outputs, inspectable output columns and semantics, and a canonical preprocessing path that can be audited instead of remaining hidden in ad hoc scripts.

In the Docker reviewer path, `sha256sum` and `git` are provided inside the container.

## Reusability Boundary

NOAA-Spec is NOAA-specific software, not a general-purpose ETL or validation framework. The substantive parsing and cleaning logic is tied to NOAA ISD / Global Hourly field structure and documentation. Some engineering patterns used here, such as contracts, provenance tracking, and deterministic fixtures, may transfer to other datasets, but that is not the primary claim of this repository snapshot.

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
