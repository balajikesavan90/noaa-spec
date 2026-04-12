# NOAA-Spec

NOAA-Spec is a Python package and repository for deterministic cleaning of NOAA Integrated Surface Database (ISD) / Global Hourly observations. Its core reusable interface is the `noaa-spec clean` command, which turns raw NOAA rows into a specification-constrained canonical CSV with explicit nulls, preserved quality codes, stable column names, and deterministic serialization.

This repository also contains broader project infrastructure around that core cleaner: domain-specific output helpers, schema contracts, quality and validation tooling, reproducibility fixtures, maintainer runbooks, and paper material. Not every directory serves the same audience. First-time users should start with the core CLI workflow, then move into the broader infrastructure only when they need it.

## What NOAA-Spec Contains

NOAA-Spec has two related layers:

| Layer | What it is | Main entry points |
| --- | --- | --- |
| Core canonicalization package | The installable package and CLI for cleaning local NOAA CSV files into deterministic canonical output. | `src/noaa_spec/cleaning.py`, `src/noaa_spec/constants.py`, `src/noaa_spec/deterministic_io.py`, `src/noaa_spec/cli.py`, `noaa-spec clean` |
| Broader repository infrastructure | Support code and documentation for domain views, schema contracts, quality reports, batch/release workflows, reproducibility checks, and maintainer research workflows. | `src/noaa_spec/domains/`, `src/noaa_spec/contract_schemas/`, `src/noaa_spec/internal/`, `tools/`, `scripts/`, `maintainer/`, `reproducibility/`, `paper/` |

The public installed command is centered on `noaa-spec clean`. The broader infrastructure is real and useful, but it is not the shortest path for a new user who wants to clean a NOAA CSV and inspect the result.

## Quick Start

> **Requires Python 3.11 or 3.12.** Python 3.13 is not currently supported. If `noaa-spec` is not on PATH after install, use `python -m noaa_spec.cli` as a fallback.

Use a supported Python environment with `venv` support:

```bash
python3.12 --version
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv
python -c "import hashlib, pathlib; print(hashlib.sha256(pathlib.Path('/tmp/station_cleaned.csv').read_bytes()).hexdigest())"
```

Expected checksum:

```text
b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

If your platform does not have a `python3.12` command, use another installed Python 3.11 or 3.12 interpreter. On Ubuntu/Debian, `venv` support may need to be installed first:

```bash
sudo apt install python3-venv
```

On Windows PowerShell:

```powershell
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv $env:TEMP\station_cleaned.csv
Get-FileHash $env:TEMP\station_cleaned.csv -Algorithm SHA256
```

If PowerShell blocks script activation, run this first:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Docker First Run

Docker provides a clean-environment reproducibility check without relying on a host-local Python setup:

```bash
docker --version
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Expected verification result:

```text
PASS: reproducibility verification succeeded.
SHA256: b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

The script is a thin wrapper around the same `noaa-spec clean` fixture workflow documented in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Minimal Workflow

The bundled raw NOAA sample in [reproducibility/minimal/station_raw.csv](reproducibility/minimal/station_raw.csv) is tracked in the repository, so the first run does not require finding outside data.

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

The canonical CSV is intentionally wide because it preserves decoded fields and QC context. For a narrower derived dataset, use a view:

```bash
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_metadata.csv --view metadata
```

Supported views:

- `metadata`
- `wind`
- `precipitation`
- `clouds_visibility`
- `pressure_temperature`
- `remarks`

The `metadata` view contains station/time context and identifying metadata rather than cleaned meteorological measurements. For compatibility, `core` and `core_meteorology` remain accepted aliases for `metadata`.

## Repository Structure

| Path | Purpose |
| --- | --- |
| `src/noaa_spec/` | Installable package code. `cleaning.py`, `constants.py`, `deterministic_io.py`, and `cli.py` are the core cleaning path. |
| `src/noaa_spec/domains/` | Domain view definitions and publishing helpers derived from the canonical dataset. |
| `src/noaa_spec/contract_schemas/` | Versioned JSON schema contracts for canonical, domain, quality-report, and manifest artifacts. |
| `src/noaa_spec/internal/` | Maintainer-oriented batch orchestration, pipeline helpers, report generation, and artifact support code. These modules are excluded from the installed package distribution. |
| `reproducibility/` | Tracked raw and expected-output fixtures plus the small reproducibility runner. |
| `docs/` | Public guides for understanding canonical output and examples. |
| `examples/` | Small runnable examples, including single-station download and clean workflow. |
| `scripts/` | Convenience scripts for reproducibility checks, audits, monitoring, and local operational workflows. |
| `tools/` | Spec coverage, reproducibility snapshot, rule-impact, and operations utilities. |
| `maintainer/` | Maintainer notes, runbooks, validation reports, architecture records, and archived planning material. |
| `paper/` | Manuscript source and bibliography. |
| `spec_sources/` | Local copies and extracted sections of NOAA format reference material used for provenance and rule work. |
| `data/`, `output/`, `artifacts/`, `noaa_file_index/` | Local runtime or generated-data areas. Treat these as working areas rather than the first-run interface. |

## Where To Start

- Users who want to clean a local NOAA CSV should install the package and run `noaa-spec clean INPUT.csv OUTPUT.csv`.
- Users who want to interpret output columns should read [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md).
- Researchers who want a reproducible starting point should use [REPRODUCIBILITY.md](REPRODUCIBILITY.md) and the tracked fixtures under [reproducibility/](reproducibility/).
- Users who want to download and clean one station should install the `fetch` extra and use [examples/download_and_clean_station.py](examples/download_and_clean_station.py).
- Developers working on schemas, domain outputs, validation reports, or larger runs should start with [CONTRIBUTING.md](CONTRIBUTING.md) and [maintainer/README.md](maintainer/README.md).
- Readers looking for the manuscript source should use [paper/README.md](paper/README.md).

## Reproducibility Path

The core reproducibility fixture is:

- Raw input: [reproducibility/minimal/station_raw.csv](reproducibility/minimal/station_raw.csv)
- Expected cleaned output: [reproducibility/minimal/station_cleaned_expected.csv](reproducibility/minimal/station_cleaned_expected.csv)
- Expected cleaned SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

Run the fixture directly:

```bash
python3 reproducibility/run_pipeline_example.py --out /tmp/noaa-spec-sample.csv
sha256sum /tmp/noaa-spec-sample.csv
```

Expected result:

```text
b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

For the full verification workflow, Docker path, and second fixture with broader field coverage, see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Optional: Download and Clean a New Station

To download and clean a single NOAA Global Hourly station from the network, install with the `fetch` extra and run the bundled example script. This requires network access and is not needed for fixture reproducibility.

```bash
python -m pip install -e ".[fetch]"
python examples/download_and_clean_station.py \
  --station 02536099999 \
  --start-year 2000 \
  --end-year 2025 \
  --output-dir output/02536099999
```

Expected outputs: `output/02536099999/Raw.csv` and `output/02536099999/Cleaned.csv`.

## Development

Install the package in editable mode, then run the tests:

```bash
python3 -m pip install -e .
python3 -m pip install pytest pytest-cov
python3 -m pytest -q
```

Development changes should preserve deterministic outputs, stable schema contracts, explicit null semantics, and NOAA rule provenance. See [CONTRIBUTING.md](CONTRIBUTING.md) for contributor guidance.

## Further Reading

- Reproducibility: [REPRODUCIBILITY.md](REPRODUCIBILITY.md)
- Output guide: [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md)
- Worked example: [docs/examples/CANONICAL_WALKTHROUGH.md](docs/examples/CANONICAL_WALKTHROUGH.md)
- Maintainer materials: [maintainer/README.md](maintainer/README.md)
