# NOAA-Spec

NOAA-Spec is a deterministic canonicalization layer for NOAA ISD / Global Hourly observations. It turns raw NOAA rows into a specification-constrained canonical CSV with explicit nulls, preserved quality codes, stable column names, and deterministic serialization.

The public software surface is the `noaa-spec clean` CLI, the canonical observation-level output contract, and the bundled checksum-backed reproducibility fixture.

## Quick Reviewer Path

Use Docker for the most reliable first review path:

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

## Public Scope

The reviewed public contribution consists only of:

- the public `noaa-spec clean` CLI
- the deterministic observation-level canonical contract
- the bundled reproducibility fixture and checksum-backed example

Other materials in this repository may support internal development, validation, or future work, but they are not part of the narrow reviewed software claim.

## Start Here

### Local Python Path

Local installation requires:

- a working Python 3.12 environment
- `venv` support

On some Linux systems, `venv` support and `ensurepip` are provided by a separate OS package. If local `venv` setup is unavailable, use the Docker path above instead of guessing.

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

Starter columns for a first pass:

- `STATION`
- `DATE`
- `temperature_c`
- `temperature_quality_code`
- `dew_point_c`
- `wind_speed_ms`
- `visibility_m`
- `TMP__qc_reason`

The canonical output is intentionally wide because it is a loss-preserving normalized representation of the source row. Most users will work with a subset of fields or a downstream domain-specific projection built from that canonical contract.

For a column-level explanation of the cleaned output, see [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md).
For one public worked example showing what a user gains from the canonical layer, see [docs/examples/CANONICAL_WALKTHROUGH.md](docs/examples/CANONICAL_WALKTHROUGH.md).

## Repository Boundary

Reviewer-visible directories such as `artifacts/`, `output/`, `data/`, `noaa_file_index/`, `tools/`, and `docs/internal/` are maintainer/supporting material. They are not required for the scoped JOSS review path above.

Tracked root CSV summaries such as `RULE_PROVENANCE_LEDGER.csv`, `spec_coverage.csv`, and related audit exports remain in the repository for maintainer workflows and internal validation. They are not part of the narrow reviewed public software surface.

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
