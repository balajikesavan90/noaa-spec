# NOAA-Spec

## What NOAA-Spec does

NOAA-Spec converts raw NOAA Integrated Surface Database (ISD) / Global Hourly records into deterministic, publication-ready artifacts. It applies specification-driven cleaning, preserves lineage from raw observations to released outputs, and produces canonical datasets, domain datasets, quality evidence, and release manifests for reproducible scientific use.

NOAA-Spec is intended for researchers and engineers working with NOAA ISD / Global Hourly data who need reproducible preprocessing pipelines.

## Why NOAA ISD is not analysis-ready

NOAA ISD observations are structurally encoded rather than analysis-ready. Raw files contain compact fixed-width fields, comma-encoded substructures, sentinel values, quality flags, and section-dependent semantics that must be interpreted from NOAA documentation before downstream analysis is trustworthy or reproducible.

## Installation

```bash
poetry install
```

Optional development install:

```bash
pip install -e .
```

Optional contributor setup:

```bash
python3 -m pip install --user --break-system-packages pytest pytest-cov
```

For cron and other scheduled jobs, install the project with Poetry and use the project-local interpreter at `.venv/bin/python` so `python -m noaa_spec.cli` works without `PYTHONPATH`.

If Poetry previously created an environment outside the repo, recreate it after switching to the project-local `.venv` layout.

Install smoke test:

```bash
./scripts/smoke_test_install.sh
```

## 5-minute example

Run the deterministic sample cleaning example:

```bash
python reproducibility/run_pipeline_example.py --out /tmp/noaa-spec-sample.csv
```

This produces a cleaned CSV at `/tmp/noaa-spec-sample.csv` with normalized fields, resolved sentinel values, and quality-filtered observations. The sample run is a reviewer-friendly smoke test of the core cleaning engine, not the final frozen submission build.

Run the installed CLI:

```bash
noaa-spec --help
```

The reproducibility example reads [sample_station_raw.txt](reproducibility/sample_station_raw.txt) and writes a cleaned CSV using the same cleaning engine exposed by the `noaa_spec` library and `noaa-spec` CLI.

## Contracts and Validation

NOAA-Spec is organized around concrete software surfaces:

- contracts that define canonical, domain, quality-report, and manifest artifact expectations,
- manifests and checksums that make release outputs auditable,
- quality reports that describe completeness, sentinel effects, and QC exclusions,
- validation tests that protect active documentation and publication-surface behavior.

The visible GitHub Actions surface is intentionally small; fuller validation expectations are documented in [docs/PIPELINE_VALIDATION_PLAN.md](docs/PIPELINE_VALIDATION_PLAN.md) and are primarily run locally before release-oriented work.

## Reviewer path

Start with [docs/REVIEWER_GUIDE.md](docs/REVIEWER_GUIDE.md). It connects installation, the sample run, artifact interpretation, and how larger validation evidence should be read during active development.

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

Not every station necessarily emits every domain artifact. A domain dataset may be absent when no rows survive that projection or when a station has no valid data for that domain after cleaning. This is expected behavior, especially for sparse domains such as precipitation.
