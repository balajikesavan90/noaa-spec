# NOAA-Spec

## What this does

NOAA-Spec is a narrow, deterministic canonicalization layer for NOAA ISD / Global Hourly observations. It turns raw NOAA observation rows into a specification-constrained canonical CSV: a loss-preserving normalized representation with explicit nulls, preserved quality codes, stable column names, and deterministic serialization.

Existing NOAA tools help users parse or access ISD data, but raw NOAA rows still contain compact encodings, sentinel values, and field-specific QC behavior that are often handled in implicit project-local preprocessing. NOAA-Spec replaces that ad hoc interpretation step with one reusable shared contract so different projects can start from the same documented canonical representation.

## What this is / What this is not

What this is:

- a deterministic canonical interpretation layer for NOAA ISD observations
- a stable intermediate representation grounded in NOAA field semantics
- a shared cleaning contract that makes preprocessing decisions explicit and reproducible

What this is not:

- a claim that every user should work directly with the full canonical table
- a general climate analytics platform
- the repository's broader publication or reporting workflows as part of the JOSS contribution boundary

## Public Scope

The reviewed public contribution consists only of:

- the public `noaa-spec clean` CLI
- the deterministic observation-level canonical contract
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

The canonical output is intentionally wide because it preserves normalized structure and provenance-bearing semantics from the source format. This is a stable intermediate representation, not a claim that the full table is the ideal direct analysis surface for every use case. Most users will work with a subset of fields or downstream derived tables built from the canonical representation.

For a column-level explanation of the cleaned output, see [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md).
For one public worked example showing what a user gains from the canonical layer, see [docs/examples/CANONICAL_WALKTHROUGH.md](docs/examples/CANONICAL_WALKTHROUGH.md).

## Reproducibility Verification

The same tracked fixture is also used for reproducibility verification:

- Raw input: [reproducibility/minimal/station_raw.csv](reproducibility/minimal/station_raw.csv)
- Raw input SHA256: `50e8bfb9ffae8278652bb7410cfbc9683a48711c35cfcf9e9dd3c38bbc403d47`
- Expected cleaned output: [reproducibility/minimal/station_cleaned_expected.csv](reproducibility/minimal/station_cleaned_expected.csv)
- Expected cleaned SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

For ordinary usage, prefer the `noaa-spec clean` CLI above. For the complete install, checksum verification, Docker clean-environment path, and explicit reproducibility boundary, use [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Docs

- Documentation index: [docs/README.md](docs/README.md)
- Reproducibility: [REPRODUCIBILITY.md](REPRODUCIBILITY.md)
- Internal maintainer docs: [docs/internal/README.md](docs/internal/README.md)
