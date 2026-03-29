# Reproducibility

This document is the authoritative public reviewer path for NOAA-Spec.

It covers:

- quick reviewer verification
- minimal local install and first run
- deterministic fixture verification
- checksum verification
- Docker clean-environment verification
- the explicit reproducibility boundary

## Quick Reviewer Path

Use Docker for the most reliable clean-environment review:

```bash
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Successful verification prints:

```text
PASS: reproducibility verification succeeded.
SHA256: b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

Inspect a small subset from the tracked canonical fixture:

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

Use [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md) if you need help interpreting the canonical columns.

## Local Python Path

Local installation requires a working Python 3.12 environment with `venv` support.

On some Linux systems, `venv` support and `ensurepip` are provided by a separate OS package. If local `venv` setup is unavailable, use the Docker path above instead of improvising a local install.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv
```

This writes the canonical NOAA-Spec representation for the tracked sample input.

Inspect a small subset of the output:

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

## Deterministic Fixture Verification

Tracked files:

- Raw input: `reproducibility/minimal/station_raw.csv`
- Raw input SHA256: `50e8bfb9ffae8278652bb7410cfbc9683a48711c35cfcf9e9dd3c38bbc403d47`
- Expected output: `reproducibility/minimal/station_cleaned_expected.csv`
- Expected output SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

Run the tracked example:

```bash
python3 reproducibility/run_pipeline_example.py --example minimal --out /tmp/noaa-spec-sample.csv
```

Verify the checksum:

```bash
sha256sum /tmp/noaa-spec-sample.csv
```

Expected result:

```text
b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

## Reproducibility Boundary

This public reproducibility surface covers only the scoped JOSS contribution:

- the public `noaa-spec clean` CLI
- the specification-constrained canonical interpretation layer
- the bundled tracked fixture and checksum-backed verification path

It does not claim reviewer reproduction of maintainer-only workflows such as:

- batch orchestration
- domain dataset publication
- release manifests
- internal validation or reporting workflows
