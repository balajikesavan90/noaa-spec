# Reproducibility

This document is the authoritative reproducibility reference for NOAA-Spec.

Views are available through the public `noaa-spec clean --view ...` CLI as optional narrower datasets for usability, but reproducibility verification for the scoped JOSS claim remains the canonical output and checksum below. The reproducible public canonical contract is the emitted CSV shown by the bundled fixture, with `STATION` and `DATE` as the reviewer-visible identifier columns.

## Quick Reviewer Path

For independent reviewer verification, use Docker:

Docker installed and running is required before these commands will work.

```bash
docker --version
```

If this command fails, Docker is not correctly installed or not available on PATH.

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

Local installation requires a working Python environment with `venv` support. NOAA-Spec currently declares support for Python `>=3.11,<3.13`; reviewers should use Python 3.11 or 3.12 for the local path. If local `venv` setup is unavailable, use Docker instead. Docker is the clean first run path for independent reviewer verification.

On any platform, if `pyarrow` does not provide a compatible wheel for the active Python version, `pip` may try to build it from source. That source-build path can fail and prevent the `noaa-spec` CLI from being installed. Use Python 3.11 or 3.12 for reviewer-local installs.

### Windows PowerShell

If PowerShell blocks script activation, run this first:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv $env:TEMP\station_cleaned.csv
Get-FileHash $env:TEMP\station_cleaned.csv -Algorithm SHA256
```

Expected SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv
python3 -c "import hashlib, pathlib; print(hashlib.sha256(pathlib.Path('/tmp/station_cleaned.csv').read_bytes()).hexdigest())"
```

Expected SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

For a narrower usability-oriented dataset, you can optionally add `--view metadata`, `--view wind`, `--view precipitation`, `--view clouds_visibility`, `--view pressure_temperature`, or `--view remarks`.

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

## Additional Fixture for Broader Field Coverage

A second tracked fixture uses station `78724099999` (8 rows, 50 raw columns) to exercise additional NOAA field structures including precipitation (AA1–AA4), multiple cloud layers (GA1–GA5), past weather (AY1/AY2), extreme temperature (KA1/KA2), and present weather (MW1–MW3).

Tracked files:

- Raw input: `reproducibility/minimal_second/station_raw.csv`
- Raw input SHA256: `7b77a6b636baaf00f465c747d541e237417757d518e13e6e286045b53d6fe685`
- Expected output: `reproducibility/minimal_second/station_cleaned_expected.csv`
- Expected output SHA256: `223efb068df6d605646a1288feedf6621fa55b4c9074c027f6347cbe7ca2f30e`

Run and verify:

```bash
noaa-spec clean reproducibility/minimal_second/station_raw.csv /tmp/second_fixture.csv
sha256sum /tmp/second_fixture.csv
```

Expected result:

```text
223efb068df6d605646a1288feedf6621fa55b4c9074c027f6347cbe7ca2f30e
```

## Reproducibility Boundary

This reproducibility surface covers the scoped JOSS contribution:

- the public `noaa-spec clean` CLI
- the specification-constrained canonical interpretation layer
- the bundled tracked fixture and checksum-backed verification path

It does not cover broader repository workflows such as batch orchestration, release manifests, or internal validation/reporting workflows.
