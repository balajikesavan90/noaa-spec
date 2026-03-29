# NOAA-Spec

## What this does

NOAA-Spec is a narrow, deterministic cleaning layer for NOAA ISD / Global Hourly observations. It turns raw NOAA observation rows into a canonical cleaned CSV: a loss-preserving normalized representation with explicit nulls, preserved quality codes, and stable column names.

Existing NOAA tools help users parse or access ISD data, but raw NOAA rows still contain compact encodings, sentinel values, and field-specific QC behavior that are not analysis-ready. NOAA-Spec packages those observation-cleaning decisions into one reusable contract so different projects can start from the same documented canonical representation.

## Public Scope

The reviewed public contribution consists only of:

- the public `noaa-spec clean` CLI
- the deterministic observation-level cleaning contract
- the bundled reproducibility fixture and checksum-backed example

Other materials in this repository may support internal development, validation, or future work, but they are not part of the narrow reviewed software claim.

## Environment

Requires Python 3.12 with `python3.12-venv` installed.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
```

## Minimal Workflow

Use the bundled raw NOAA sample in [reproducibility/minimal/station_raw.csv](reproducibility/minimal/station_raw.csv). It is tracked in the repository, so the workflow is runnable without finding outside data first.

Run the public CLI:

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

The canonical cleaned output is intentionally wide because it preserves observational structure, QC context, and normalized field semantics in one deterministic source-of-truth layer. Most downstream work will select a relevant subset of columns, and broader repository workflows can also project canonical observations into narrower domain datasets.

For a column-level explanation of the cleaned output, see [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md).

## Reproducibility Verification

The same tracked fixture is also used for reproducibility verification:

- Raw input: [reproducibility/minimal/station_raw.csv](reproducibility/minimal/station_raw.csv)
- Raw input SHA256: `50e8bfb9ffae8278652bb7410cfbc9683a48711c35cfcf9e9dd3c38bbc403d47`
- Expected cleaned output: [reproducibility/minimal/station_cleaned_expected.csv](reproducibility/minimal/station_cleaned_expected.csv)
- Expected cleaned SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

For ordinary usage, prefer the `noaa-spec clean` CLI above. For reviewer-oriented checksum verification, run:

```bash
python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
```

That verification path, including the Docker-based clean-environment check for reviewers, is documented in [reproducibility/README.md](reproducibility/README.md).

## Docs

- Documentation index: [docs/README.md](docs/README.md)
- Reproducibility: [reproducibility/README.md](reproducibility/README.md)
- Internal maintainer docs: [docs/internal/README.md](docs/internal/README.md)
