# NOAA-Spec

## What this does

This package provides a reusable, deterministic canonical cleaning layer for NOAA ISD / Global Hourly data, standardizing sentinel handling, QC semantics, and output schema beyond existing parsing-focused tools.

We are not aware of any existing reusable NOAA ISD cleaning layer that provides a stable observation-level contract.

NOAA-Spec is a focused cleaning tool. It turns raw NOAA observation rows into a deterministic cleaned CSV with explicit nulls, preserved quality codes, and stable column names that downstream analysis can rely on.

## Environment

Requires Python 3.12 with `python3.12-venv` installed.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

## Minimal Real Workflow

Use the bundled raw NOAA sample in [reproducibility/minimal/station_raw.csv](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/reproducibility/minimal/station_raw.csv). It is tracked in the repository, so the workflow is runnable without finding outside data first.

Clean it with the public CLI:

```bash
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv
```

Before:

```text
DATE                 TMP      DEW      VIS
2000-01-10T06:00:00  +0180,1  +0100,1  010000,1,N,1
2000-03-17T09:00:00  +9999,9  +9999,9  999999,9,N,1
```

After:

```text
DATE                 temperature_c  temperature_quality_code  dew_point_c  visibility_m  TMP__qc_reason
2000-01-10T06:00:00  18.0           1                         10.0         10000.0       NaN
2000-03-17T09:00:00  NaN            9                         NaN          NaN           SENTINEL_MISSING
```

Key transformations:

- Sentinel-coded values such as `+9999,9` become nulls instead of fake measurements.
- NOAA QC semantics are preserved in separate fields such as `temperature_quality_code`.
- Output columns are normalized into a stable observation-level schema such as `temperature_c`, `dew_point_c`, and `visibility_m`.

## Reproducible Example

The curated reproducibility fixture is fully tracked in-repo:

- Raw input: [reproducibility/minimal/station_raw.csv](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/reproducibility/minimal/station_raw.csv)
- Raw input SHA256: `50e8bfb9ffae8278652bb7410cfbc9683a48711c35cfcf9e9dd3c38bbc403d47`
- Expected cleaned output: [reproducibility/minimal/station_cleaned_expected.csv](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/reproducibility/minimal/station_cleaned_expected.csv)
- Expected cleaned SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

Exact command used:

```bash
python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
```

The reproducibility workflow and checksum verification are documented in [reproducibility/README.md](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/reproducibility/README.md).

## Why this exists

Existing NOAA tools help users parse or access ISD data, but raw NOAA rows still contain compact encodings, sentinel values, and field-specific QC behavior that are not analysis-ready. NOAA-Spec packages those cleaning decisions into one reusable surface so different projects can start from the same documented observation-level output.

## Scope

The public surface is intentionally small:

- library cleaning code under [src/noaa_spec](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/src/noaa_spec)
- the public `noaa-spec clean` command
- the reproducible example under [reproducibility/](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/reproducibility)

Batch orchestration, domain splitting, manifests, and report-generation material are maintainer-facing and live behind internal docs or the internal CLI.

## Docs

- Output guide: [docs/UNDERSTANDING_OUTPUT.md](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/docs/UNDERSTANDING_OUTPUT.md)
- Reproducibility: [reproducibility/README.md](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/reproducibility/README.md)
- Internal maintainer docs: [docs/internal/README.md](/home/balaji-kesavan/Documents/AI_Projects/noaa-climate-data/docs/internal/README.md)
