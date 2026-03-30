# NOAA-Spec

NOAA-Spec is a deterministic canonicalization layer for NOAA ISD / Global Hourly observations. It turns raw NOAA rows into a specification-constrained canonical CSV with explicit nulls, preserved quality codes, stable column names, and deterministic serialization.

The public software surface is the `noaa-spec clean` CLI, the canonical observation-level output contract, optional secondary views derived from the canonical output, and the bundled checksum-backed reproducibility fixture.

## Quick Reviewer Path

For independent reviewer verification, use Docker:

```bash
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Expected verification result:

```text
PASS: reproducibility verification succeeded.
SHA256: b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

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

For column interpretation, start with [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md).

## Getting Started (Recommended)

For first-time use, start with a view derived from the canonical output:

```bash
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_core.csv --view core
```

Other supported views:

- `core` (`core_meteorology`)
- `wind`
- `precipitation`
- `clouds_visibility`
- `pressure_temperature`
- `remarks`

How to think about them:

- The canonical CSV remains the primary, loss-preserving contract.
- Views are secondary projections derived from that canonical output for usability.
- Most users can start with a view, then rerun without `--view` when they need the full canonical table.

## Public Scope

The reviewed public contribution consists only of:

- the public `noaa-spec clean` CLI
- the deterministic observation-level canonical contract
- secondary views derived from the canonical output
- the bundled reproducibility fixture and checksum-backed example

The JOSS-facing contribution is this deterministic interpretation layer and its reproducibility path.

## Optional Local Install

Local installation is a convenience path for users and developers. The reviewer-verified path is the Docker workflow above.

Local installation requires:

- a working Python 3.12 environment
- `venv` support

On some Linux systems, `venv` support and `ensurepip` are provided by a separate OS package. If local `venv` setup is unavailable, use Docker instead of improvising a host-local reviewer path.

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

Two competent researchers can start from the same raw NOAA row and still diverge before analysis begins.

- One script may turn `TMP=+9999,9` into a numeric placeholder and drop the `9` quality code.
- Another may convert the temperature to null but never preserve why it became null.
- A third may decode `VIS=999999,9,N,1` differently again.

Those are not modeling choices yet. They are interpretation choices hidden inside preprocessing. NOAA-Spec fixes that step by emitting one deterministic canonical row with nullified sentinels, preserved QC semantics, and stable column names. Different downstream filters can still differ, but they begin from the same interpretation layer instead of from incompatible local cleaning rules.

## Why The Canonical Contract Is Reusable

The gain is not only "cleaned data." The same canonical row can support different downstream policies without each user re-implementing NOAA decoding rules first.

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

The canonical output is intentionally wide because it is a loss-preserving normalized representation of the source row. Most users should not begin by reading all columns at once. Start with a subset of fields or with one of the domain splits built from the canonical contract, such as `core_meteorology`, `wind`, `precipitation`, `clouds_visibility`, `pressure_temperature`, or `remarks`.

If you want NOAA-Spec to write one of those narrower projections directly, use `--view`. For example:

```bash
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_pressure_temperature.csv --view pressure_temperature
```

For a column-level explanation of the cleaned output, see [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md).
For one public worked example showing what a user gains from the canonical layer, see [docs/examples/CANONICAL_WALKTHROUGH.md](docs/examples/CANONICAL_WALKTHROUGH.md).

## Repository Boundary

Reviewer-facing materials are this README, [REPRODUCIBILITY.md](REPRODUCIBILITY.md), `src/noaa_spec`, `tests`, the tracked fixture under `reproducibility/minimal/`, and the public docs under `docs/`.

Additional repository material may support broader maintenance and publication workflows, but the JOSS claim here is the canonical interpretation layer above.

## Reproducibility Verification

The same tracked fixture is also used for reproducibility verification:

- Raw input: [reproducibility/minimal/station_raw.csv](reproducibility/minimal/station_raw.csv)
- Raw input SHA256: `50e8bfb9ffae8278652bb7410cfbc9683a48711c35cfcf9e9dd3c38bbc403d47`
- Expected cleaned output: [reproducibility/minimal/station_cleaned_expected.csv](reproducibility/minimal/station_cleaned_expected.csv)
- Expected cleaned SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

For ordinary usage, prefer the `noaa-spec clean` CLI above. For the complete install, checksum verification, Docker clean-environment path, and explicit reproducibility boundary, use [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Docs

- Reproducibility: [REPRODUCIBILITY.md](REPRODUCIBILITY.md)
- Output guide: [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md)
- Worked example: [docs/examples/CANONICAL_WALKTHROUGH.md](docs/examples/CANONICAL_WALKTHROUGH.md)
