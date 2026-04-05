# Reproducibility

This document is the authoritative reproducibility reference for NOAA-Spec.

Views are available through the public `noaa-spec clean --view ...` CLI as optional usability projections, but reproducibility verification for the scoped JOSS claim remains the canonical output and checksum below. The reproducible public canonical contract is the emitted CSV shown by the bundled fixture, with `STATION` and `DATE` as the reviewer-visible identifier columns.

## Quick Reviewer Path

For independent reviewer verification, use Docker:

```bash
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Successful verification prints:

```text
PASS: reproducibility verification succeeded.
SHA256: b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

## Optional Local Install

Local installation is a convenience path for users and developers. It is not the authoritative reviewer path.

Local installation requires a working Python 3.12 environment with `venv` support. If local `venv` setup is unavailable, use Docker instead.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv
```

For a narrower usability-oriented projection, you can optionally add `--view metadata`, `--view wind`, `--view precipitation`, `--view clouds_visibility`, `--view pressure_temperature`, or `--view remarks`.

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

## Deterministic Fixture Verification

Tracked files:

- Raw input: `reproducibility/minimal/station_raw.csv`
- Raw input SHA256: `50e8bfb9ffae8278652bb7410cfbc9683a48711c35cfcf9e9dd3c38bbc403d47`
- Expected output: `reproducibility/minimal/station_cleaned_expected.csv`
- Expected output SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

Run the tracked example:

```bash
python3 reproducibility/run_pipeline_example.py --out /tmp/noaa-spec-sample.csv
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

This reproducibility surface covers the scoped JOSS contribution:

- the public `noaa-spec clean` CLI
- the specification-constrained canonical interpretation layer
- the bundled tracked fixture and checksum-backed verification path

It does not cover broader repository workflows such as batch orchestration, release manifests, or internal validation/reporting workflows.
