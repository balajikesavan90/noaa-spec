# NOAA-Spec

## What NOAA-Spec does

NOAA-Spec converts raw NOAA Integrated Surface Database (ISD) / Global Hourly records into deterministic, publication-ready data artifacts. It applies specification-driven cleaning, preserves lineage from raw observations to released outputs, and produces canonical datasets, domain datasets, quality evidence, and release manifests for reproducible scientific use.

## Why NOAA ISD is not analysis-ready

NOAA ISD observations are structurally encoded rather than analysis-ready. Raw files contain compact fixed-width fields, comma-encoded substructures, sentinel values, quality flags, and section-dependent semantics that must be interpreted from NOAA documentation before downstream analysis is trustworthy or reproducible.

## Installation

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

Run the installed CLI:

```bash
noaa-spec --help
```

The reproducibility example reads [sample_station_raw.txt](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/reproducibility/sample_station_raw.txt) and writes a cleaned CSV using the same cleaning engine exposed by the library and CLI.

## Verification Triangle

NOAA-Spec is built around a verification-first model:

- NOAA specification sources are parsed into explicit rule inventories.
- Implementation behavior is tied to those rules in code and provenance artifacts.
- Tests and quality reports check that documentation, implementation, and outputs stay aligned.

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

- JOSS paper source: [paper/paper.md](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/paper/paper.md)
- Docs index: [docs/README.md](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/docs/README.md)
- Reproducibility notes: [reproducibility/README.md](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/reproducibility/README.md)
- Minimal examples: [examples/README.md](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/examples/README.md)
