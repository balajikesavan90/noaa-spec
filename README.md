# NOAA-Spec

## What NOAA-Spec does

NOAA-Spec converts raw NOAA Integrated Surface Database (ISD) / Global Hourly records into deterministic, publication-ready artifacts. In this repository snapshot, the reviewer-verifiable surface is the canonical cleaning pipeline plus deterministic output verification on a tracked sample input.

NOAA-Spec is intended for researchers and engineers working with NOAA ISD / Global Hourly data who need reproducible preprocessing pipelines.

## Why NOAA ISD is not analysis-ready

NOAA ISD observations are structurally encoded rather than analysis-ready. Raw files contain compact fixed-width fields, comma-encoded substructures, sentinel values, quality flags, and section-dependent semantics that must be interpreted from NOAA documentation before downstream analysis is trustworthy or reproducible.

## Installation

Tested on Linux with `Python 3.12`.

Network access is required for the Poetry installer and dependency resolution.

Linux prerequisites:

- `python3`
- `curl`
- virtual environment support for your Python installation
- Debian/Ubuntu-like systems commonly need `python3-venv`

This project relies on `poetry.lock` for deterministic dependency resolution. Do not regenerate it unless you are intentionally updating dependencies.

Primary reviewer install path:

```bash
python3 --version
curl --version
curl -sSL https://install.python-poetry.org | python3 - --version 2.1.3
export PATH="$HOME/.local/bin:$PATH"
poetry --version
poetry install
```

If this checkout already contains a leftover `.venv` from an older revision, remove it before running `poetry install`. The reviewer quickstart does not use an in-project virtual environment.

All documented project commands below are run through Poetry. Do not rely on a global `noaa-spec` install.

## Reviewer Quickstart (3 Steps)

1. Install dependencies with the Poetry path above.

2. Run the minimal reproducibility example:

```bash
poetry run python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
```

3. Verify the output checksum against the tracked expected artifact:

```bash
bash scripts/verify_reproducibility.sh
```

Manual checksum verification is also available:

```bash
sha256sum /tmp/noaa-spec-sample.csv
sha256sum reproducibility/minimal/station_cleaned_expected.csv
```

Expected SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

The default reproducibility example reads [station_raw.csv](reproducibility/minimal/station_raw.csv) and writes a cleaned CSV using the same cleaning engine exposed by the `noaa_spec` library and the `noaa-spec` CLI. The reviewer path writes to `/tmp`, not to tracked repository files.

## Supported Reviewer Commands

These are the reviewer commands for this repository snapshot:

```bash
poetry run noaa-spec --help
poetry run python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
bash scripts/verify_reproducibility.sh
poetry run pytest -q
```

Success means:

- `poetry run noaa-spec --help` exits successfully
- `bash scripts/verify_reproducibility.sh` prints `PASS:` and the expected SHA256
- `poetry run pytest -q` completes in the same Poetry-managed environment

## Reproducibility Boundary

This revision demonstrates deterministic, specification-constrained cleaning at bounded scale using tracked reproducibility fixtures. Full release-scale artifacts are part of the broader publication workflow but are not bundled as reviewer evidence in this development snapshot.

No archived release bundle is linked for this revision. Reviewers should rely on:

- the minimal reproducibility example in `reproducibility/minimal/`
- deterministic checksum verification
- the test suite and documentation checks

## Contracts and Validation

NOAA-Spec is organized around concrete software surfaces:

- contracts that define canonical, domain, quality-report, and manifest artifact expectations,
- manifests with portable relative artifact paths and content checksums that make release outputs auditable,
- quality reports that describe completeness, sentinel effects, and QC exclusions,
- validation tests that protect active documentation and publication-surface behavior.

The visible GitHub Actions surface is intentionally small; fuller validation expectations are documented in [docs/PIPELINE_VALIDATION_PLAN.md](docs/PIPELINE_VALIDATION_PLAN.md) and are primarily run locally before release-oriented work.

## When to use / when not to use

Use NOAA-Spec when you need:

- deterministic preprocessing of NOAA ISD / Global Hourly data
- publication-grade cleaned outputs with schema contracts
- traceable cleaning rules and quality evidence
- reproducible release artifacts for research workflows

Do not use NOAA-Spec when you need:

- a generic ETL framework for unrelated datasets
- opinionated downstream climate analysis or modeling workflows
- silent heuristic repair of ambiguous source data

## Paper and docs links

- Reviewer guide: [docs/REVIEWER_GUIDE.md](docs/REVIEWER_GUIDE.md)
- JOSS paper source: [paper/paper.md](paper/paper.md)
- Docs index: [docs/README.md](docs/README.md)
- Reproducibility notes: [reproducibility/README.md](reproducibility/README.md)
- Example scripts: [examples/README.md](examples/README.md)

Not every station necessarily emits every domain artifact. A domain dataset may be absent when no rows survive that projection or when a station has no valid data for that domain after cleaning. This is expected behavior, especially for sparse domains such as precipitation.
