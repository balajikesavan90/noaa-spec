# NOAA-Spec

NOAA-Spec is a deterministic canonicalization layer for NOAA ISD / Global Hourly observations. It turns raw NOAA rows into a specification-constrained canonical CSV with explicit nulls, preserved quality codes, stable column names, and deterministic serialization.

The public software surface is the `noaa-spec clean` CLI, the canonical observation-level output contract, a small set of optional derived views, and the bundled checksum-backed reproducibility fixture.

## Public Scope

The public contribution consists of:

- the public `noaa-spec clean` CLI
- the deterministic observation-level canonical contract
- optional views derived from the canonical output
- the bundled reproducibility fixture and checksum-backed example

The JOSS-facing contribution is a shared deterministic interpretation layer for NOAA rows and a reproducibility path reviewers can run directly from this repository.
The reproducible public canonical contract is the CSV emitted by `noaa-spec clean` and exemplified by `reproducibility/minimal/station_cleaned_expected.csv`; its reviewer-visible identifier columns are `STATION` and `DATE`.

## Repository Scope

This repository contains both the public NOAA-Spec software surface and some maintainer-internal support material.

For JOSS review and normal first-time use, the relevant surface is:

- `src/noaa_spec/` — the installable package and `noaa-spec clean` CLI
- `reproducibility/` — the tracked fixture and checksum-backed verification
- `docs/` — output guide and worked example
- `paper/` — the JOSS manuscript
- `README.md` and `REPRODUCIBILITY.md`

The following directories are **maintainer-internal** support material. They are not required for the reviewer path, not part of the public API, and not the subject of the JOSS submission:

- `maintainer/` — internal planning docs, audit records, and operational guides
- `tools/` — internal spec-coverage and rule-impact tooling
- `spec_sources/` — reference copies of the NOAA ISD format specification used during development

Within `src/noaa_spec/`, the **public surface** is the `noaa-spec clean` CLI and the canonical cleaning contract (`cleaning.py`, `constants.py`, `deterministic_io.py`, `domains/`). Additional modules (`pipeline.py`, `cleaning_runner.py`, `internal/`, `research_reports.py`, `noaa_client.py`) support maintainer batch workflows and are not required for normal use or JOSS evaluation.

## Docker First Run

For independent reviewer verification and the cleanest first run, use Docker:

```bash
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Expected verification result:

```text
PASS: reproducibility verification succeeded.
SHA256: b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

This is the recommended reviewer-safe path. It reruns the tracked reproducibility fixture and verifies the canonical contract checksum without depending on a host-local Python setup.

## Optional Local Install

For ordinary local use, install NOAA-Spec into a Python 3.12 environment with `venv` support.

On some Linux systems, `venv` support and `ensurepip` are provided by a separate OS package. If local `venv` setup is unavailable, use the Docker path above instead of improvising a host-local reviewer path.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv
sha256sum /tmp/station_cleaned.csv
```

Expected checksum:

```text
b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

Inspect a small reviewer-friendly subset:

```bash
python3 - <<'PY'
import csv

cols = [
    "STATION",
    "DATE",
    "temperature_c",
    "temperature_quality_code",
    "visibility_m",
    "TMP__qc_reason",
]

with open("/tmp/station_cleaned.csv", newline="", encoding="utf-8") as handle:
    reader = csv.DictReader(handle)
    for row in list(reader)[:5]:
        print({col: row[col] for col in cols})
PY
```

## Run The Canonical Contract

The canonical dataset defines the reproducible interpretation contract. In that public canonical CSV, the station identifier remains `STATION`, matching the bundled fixture and CLI output. Optional `--view` outputs are derived projections for usability and do not modify the underlying contract.

Run the canonical workflow first:

```bash
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv
```

For a first inspection path, many users begin with a smaller derived view:

```bash
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_metadata.csv --view metadata
```

The canonical CSV is the full loss-preserving contract and is intentionally wide. Optional views are usability projections derived from that canonical output, so you can orient yourself quickly and then expand into the full canonical columns as needed.

## Optional Derived Views

If you want NOAA-Spec to write a narrower derived projection directly, add `--view` after the canonical workflow above.

Other supported views:

- `metadata`
- `wind`
- `precipitation`
- `clouds_visibility`
- `pressure_temperature`
- `remarks`

The `metadata` view contains station/time context and identifying metadata rather than cleaned meteorological measurements. The canonical CSV remains the primary contract. Views are optional convenience projections derived from that canonical output.

For compatibility, `core` and `core_meteorology` remain accepted aliases for `metadata`.

## Minimal Workflow

Use the bundled raw NOAA sample in [reproducibility/minimal/station_raw.csv](reproducibility/minimal/station_raw.csv). It is tracked in the repository, so the workflow is runnable without finding outside data first.

Raw snippet:

```text
DATE                 TMP      DEW      VIS
2000-01-10T06:00:00  +0180,1  +0100,1  010000,1,N,1
2000-03-17T09:00:00  +9999,9  +9999,9  999999,9,N,1
```

Canonical subset:

```text
DATE                 temperature_c  temperature_quality_code  dew_point_c  visibility_m  TMP__qc_reason
2000-01-10T06:00:00  18.0           1                         10.0         10000.0       NaN
2000-03-17T09:00:00  NaN            9                         NaN          NaN           SENTINEL_MISSING
```

Key transformations:

- Sentinel-coded values such as `+9999,9` become nulls instead of fake measurements.
- NOAA QC semantics are preserved in separate fields such as `temperature_quality_code`.
- Output columns are normalized into a stable observation-level schema such as `temperature_c`, `dew_point_c`, and `visibility_m`.

## Why This Matters In Practice

Raw NOAA token:

```text
TMP=+9999,9
```

Ad hoc workflow:

```text
temperature = NaN
```

NOAA-Spec canonical workflow:

```text
temperature_c = null
temperature_quality_code = 9
TMP__qc_reason = SENTINEL_MISSING
```

Ad hoc preprocessing often keeps only the missing temperature and discards the QC context that explains why it is missing. NOAA-Spec preserves that sidecar context deterministically, so downstream users can distinguish sentinel-coded missingness from later quality-based filtering and start from the same decoded interpretation instead of silently diverging.

## Why The Canonical Contract Is Reusable

The gain is not only "cleaned data." NOAA decoding and cleaning logic is often reimplemented locally across projects; the same canonical row lets multiple downstream workflows begin from one shared interpretation instead of rebuilding that logic independently.

Shared canonical subset:

```text
STATION,DATE,temperature_c,temperature_quality_code,visibility_m,TMP__qc_reason
40435099999,2000-01-10T06:00:00,18.0,1,10000.0,
40435099999,2000-03-17T09:00:00,,9,,SENTINEL_MISSING
```

Two downstream users can start from the same columns:

- User A keeps rows where `temperature_c` is present.
- User B keeps rows where `temperature_c` is present and `temperature_quality_code == 1`.

Both users reuse the same deterministic interpretation of `TMP=+9999,9` and `VIS=999999,9,N,1`. Without the canonical contract, each script has to decode sentinels, preserve QC state, and normalize packed field names on its own before those downstream choices can even begin.

Starter columns for a first pass:

- `STATION`
- `DATE`
- `temperature_c`
- `temperature_quality_code`
- `dew_point_c`
- `wind_speed_ms`
- `visibility_m`
- `TMP__qc_reason`

The canonical output is intentionally wide because it is a loss-preserving normalized representation of the source row. Most users should not begin by reading all columns at once. Start with the canonical contract, inspect a subset of fields, and use an optional `--view` projection when a narrower convenience output is helpful.

For a column-level explanation of the cleaned output, see [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md).
For one public worked example showing what a user gains from the canonical layer, see [docs/examples/CANONICAL_WALKTHROUGH.md](docs/examples/CANONICAL_WALKTHROUGH.md).

## Repository Boundary

Reviewer-facing materials are this README, [REPRODUCIBILITY.md](REPRODUCIBILITY.md), the tracked fixture under `reproducibility/minimal/`, the public docs under `docs/`, and the public package under `src/noaa_spec`. See [Repository Scope](#repository-scope) above for the full public/maintainer-internal boundary.

## Quick Reviewer Inspection

Inspect a small, reviewer-friendly subset from the tracked canonical fixture:

```bash
python3 - <<'PY'
import csv

cols = [
    "STATION",
    "DATE",
    "temperature_c",
    "temperature_quality_code",
    "visibility_m",
    "TMP__qc_reason",
]

with open("reproducibility/minimal/station_cleaned_expected.csv", newline="", encoding="utf-8") as handle:
    reader = csv.DictReader(handle)
    for row in list(reader)[:5]:
        print({col: row[col] for col in cols})
PY
```

## Reproducibility Verification

The same tracked fixture is also used for reproducibility verification:

- Raw input: [reproducibility/minimal/station_raw.csv](reproducibility/minimal/station_raw.csv)
- Raw input SHA256: `50e8bfb9ffae8278652bb7410cfbc9683a48711c35cfcf9e9dd3c38bbc403d47`
- Expected cleaned output: [reproducibility/minimal/station_cleaned_expected.csv](reproducibility/minimal/station_cleaned_expected.csv)
- Expected cleaned SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

The included fixture is intentionally minimal (5 rows) and serves as a deterministic reproducibility proof. Larger-scale processing is supported but not bundled in-repo.

For the complete checksum verification, Docker clean-environment path, and explicit reproducibility boundary, use [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Docs

- Reproducibility: [REPRODUCIBILITY.md](REPRODUCIBILITY.md)
- Output guide: [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md)
- Worked example: [docs/examples/CANONICAL_WALKTHROUGH.md](docs/examples/CANONICAL_WALKTHROUGH.md)
