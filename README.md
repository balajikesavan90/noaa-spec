# NOAA-Spec

## What NOAA-Spec does

NOAA-Spec converts raw NOAA Integrated Surface Database (ISD) / Global Hourly records into deterministic, publication-ready artifacts. It applies specification-driven cleaning, preserves lineage from raw observations to released outputs, and produces canonical datasets, domain datasets, quality evidence, and release manifests for reproducible scientific use.

NOAA-Spec is intended for researchers and engineers working with NOAA ISD / Global Hourly data who need reproducible preprocessing pipelines.

## Why NOAA ISD is not analysis-ready

NOAA ISD observations are structurally encoded rather than analysis-ready. Raw files contain compact fixed-width fields, comma-encoded substructures, sentinel values, quality flags, and section-dependent semantics that must be interpreted from NOAA documentation before downstream analysis is trustworthy or reproducible.

## Installation

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
- the official Poetry installer is an acceptable alternative, but this repository documents `pipx` as the primary reviewer path

All documented project commands below are run through Poetry. Do not rely on a global `noaa-spec` install or a repo-local `.venv/bin/python` path.

Install smoke test:

```bash
bash scripts/smoke_test_install.sh
```

## 5-minute example

From a clean environment, the shortest reviewer path is:

```bash
poetry run python reproducibility/run_pipeline_example.py --out /tmp/noaa-spec-sample.csv
```

Verify that the installed CLI is available:

```bash
poetry run noaa-spec --help
```

This produces a cleaned CSV at `/tmp/noaa-spec-sample.csv` with normalized fields, resolved sentinel values, and quality-filtered observations. The sample run is the reproducible in-repo example. It is intentionally small and is not a substitute for larger external release builds.

The reproducibility example reads [sample_station_raw.txt](reproducibility/sample_station_raw.txt) and writes a cleaned CSV using the same cleaning engine exposed by the `noaa_spec` library and the `noaa-spec` CLI. The reviewer path writes to `/tmp`, not to tracked repository files, and should exit without `[PARSE_STRICT]` warnings.

## Contracts and Validation

NOAA-Spec is organized around concrete software surfaces:

- contracts that define canonical, domain, quality-report, and manifest artifact expectations,
- manifests with portable relative artifact paths and content checksums that make release outputs auditable,
- quality reports that describe completeness, sentinel effects, and QC exclusions,
- validation tests that protect active documentation and publication-surface behavior.

The visible GitHub Actions surface is intentionally small; fuller validation expectations are documented in [docs/PIPELINE_VALIDATION_PLAN.md](docs/PIPELINE_VALIDATION_PLAN.md) and are primarily run locally before release-oriented work.

## Reviewer path

Start with [docs/REVIEWER_GUIDE.md](docs/REVIEWER_GUIDE.md). It gives the exact install, sample run, verification, and artifact-boundary path for reviewers working from a clean checkout.

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
- Minimal examples: [examples/README.md](examples/README.md)

What is reproducible from this repository:

- `poetry install`
- the bounded sample run in `reproducibility/`
- the test suite and validation docs

What is not bundled as part of this active-development checkout:

- large external release builds
- machine-local archives
- reviewer-irrelevant runtime leftovers

Not every station necessarily emits every domain artifact. A domain dataset may be absent when no rows survive that projection or when a station has no valid data for that domain after cleaning. This is expected behavior, especially for sparse domains such as precipitation.
