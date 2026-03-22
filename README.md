# NOAA-Spec

## What NOAA-Spec does

NOAA-Spec converts raw NOAA Integrated Surface Database (ISD) / Global Hourly records into deterministic, publication-ready artifacts. It applies specification-driven cleaning, preserves lineage from raw observations to released outputs, and produces canonical datasets, domain datasets, quality evidence, and release manifests for reproducible scientific use.

NOAA-Spec is intended for researchers and engineers working with NOAA ISD / Global Hourly data who need reproducible preprocessing pipelines.

## Why NOAA ISD is not analysis-ready

NOAA ISD observations are structurally encoded rather than analysis-ready. Raw files contain compact fixed-width fields, comma-encoded substructures, sentinel values, quality flags, and section-dependent semantics that must be interpreted from NOAA documentation before downstream analysis is trustworthy or reproducible.

## Installation

```bash
pip install .
```

Optional development install:

```bash
pip install -e .
```

Optional contributor setup:

```bash
python3 -m pip install --user --break-system-packages pytest pytest-cov
```

## 5-minute example

Run the deterministic sample cleaning example:

```bash
python reproducibility/run_pipeline_example.py --out /tmp/noaa-spec-sample.csv
```

This produces a cleaned CSV at `/tmp/noaa-spec-sample.csv` with normalized fields, resolved sentinel values, and quality-filtered observations.

Run the installed CLI:

```bash
noaa-spec --help
```

The reproducibility example reads [sample_station_raw.txt](reproducibility/sample_station_raw.txt) and writes a cleaned CSV using the same cleaning engine exposed by the `noaa_spec` library and `noaa-spec` CLI.

## Verification Triangle

NOAA-Spec is built around a concrete specification-to-output validation model:

- NOAA specifications are translated into formal rule inventories.
- Implementation behavior is explicitly mapped to those rules in code and provenance artifacts.
- Outputs are validated with tests and quality artifacts to keep documentation, implementation, and released data aligned.

This keeps the system focused on transparent, deterministic preprocessing rather than ad hoc data munging.

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

- JOSS paper source: [paper/paper.md](paper/paper.md)
- Docs index: [docs/README.md](docs/README.md)
- Reproducibility notes: [reproducibility/README.md](reproducibility/README.md)
- Minimal examples: [examples/README.md](examples/README.md)
