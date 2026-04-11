# NOAA-Spec

NOAA-Spec is a deterministic canonicalization layer for NOAA ISD / Global Hourly observations. It turns raw NOAA rows into a specification-constrained canonical CSV with explicit nulls, preserved quality codes, stable column names, and deterministic serialization.

High-level pipeline overview:

```mermaid
flowchart TB
    A["Raw NOAA ISD /<br/>Global Hourly input"]
    B["Specification-constrained<br/>parsing"]
    C["Specification-driven<br/>validation<br/>(rule enforcement)"]
    D["Canonical, loss-preserving<br/>cleaned dataset"]
    E["Optional domain-specific<br/>datasets"]
    F["Quality reports, manifests,<br/>and provenance artifacts"]

    A --> B --> C --> D
    D --> E
    D --> F
```

NOAA-Spec transforms raw NOAA observations into a canonical cleaned representation governed by specification-derived rules. That canonical dataset is the source layer for optional domain-specific datasets and for deterministic downstream artifacts such as quality reports, release manifests, and related provenance records.

## JOSS Scope — Start Here

**The JOSS submission is the `noaa-spec clean` CLI, its canonical output contract, and the bundled checksum-backed reproducibility fixture.** That is the reviewed surface.

| In scope (JOSS-reviewed) | Not in scope |
| --- | --- |
| `src/noaa_spec/` — installable package and CLI | `maintainer/` — internal planning and audit docs |
| `reproducibility/` — tracked fixture and verification | `tools/` — internal spec-coverage tooling |
| `docs/` — output guide and worked example | `spec_sources/` — NOAA format reference copies |
| `paper/` — JOSS manuscript | `scripts/` — operational and batch-run helpers |
| `README.md`, `REPRODUCIBILITY.md` | `noaa_file_index/`, `output/`, `data/` — local data |

**Public API surface.** Within `src/noaa_spec/`, the public surface is:

- `cleaning.py` — canonical interpretation logic
- `constants.py` — field rules, sentinels, and QC definitions
- `deterministic_io.py` — checksummable CSV writer
- `cli.py` — the `noaa-spec clean` entry point
- `noaa_client.py` — public NOAA Global Hourly download helpers for single-station workflows
- `domains/` — view definitions for domain-specific datasets

The internal CLI and pipeline modules (`internal/`, `pipeline.py`, and related batch helpers) are maintainer-oriented. They are used for large-scale batch processing, are not required for standard usage, and may not be cross-platform. The [single-station example script](examples/download_and_clean_station.py) is the recommended cross-platform workflow for downloading and cleaning one station.

## Docker First Run

For independent reviewer verification and the cleanest first run, use Docker:

Docker installed and running is required before these commands will work.

```bash
docker --version
```

If this command fails, Docker is not correctly installed or not available on PATH.

```bash
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Expected verification result:

```text
PASS: reproducibility verification succeeded.
SHA256: b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

This is the recommended reviewer-safe path for independent reviewer verification and a clean first run. It reruns the tracked reproducibility fixture and verifies the canonical contract checksum without depending on a host-local Python setup.

## Optional Local Install

For ordinary local use, install NOAA-Spec into a Python 3.12 environment with `venv` support. This is the normal user/developer workflow, not the independent reviewer verification path.

If local `venv` setup is unavailable or inconvenient, use the Docker path above instead.

The base install is sufficient for cleaning existing local NOAA CSV files with `noaa-spec clean`. Downloading NOAA data also requires the `fetch` optional dependency, which installs `requests`. The base install already includes `pandas` and `pyarrow`.

### Windows PowerShell

If PowerShell blocks script activation, run this first:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv $env:TEMP\station_cleaned.csv
Get-FileHash $env:TEMP\station_cleaned.csv -Algorithm SHA256
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv
sha256sum /tmp/station_cleaned.csv
```

### Ubuntu / Debian Note

Ubuntu/Debian users may need to install `venv` support first:

```bash
sudo apt install python3-venv
```

Expected checksum: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

## Download and clean a single station (recommended workflow)

This is the recommended public entry point when you want NOAA-Spec to download a single NOAA Global Hourly station and clean it end to end. It uses only public package modules and does not use the maintainer-oriented internal CLI or pipeline modules.

Install with the download extra:

```bash
python -m pip install -e ".[fetch]"
```

Then run:

```bash
python examples/download_and_clean_station.py \
  --station 02536099999 \
  --start-year 2000 \
  --end-year 2025 \
  --output-dir output/02536099999
```

On Windows PowerShell, the same command can be written on one line:

```powershell
python examples/download_and_clean_station.py --station 02536099999 --start-year 2000 --end-year 2025 --output-dir output\02536099999
```

Expected outputs:

```text
output/
  02536099999/
    Raw.csv
    Cleaned.csv
```

`Raw.csv` contains the downloaded NOAA Global Hourly rows for the station and year range. `Cleaned.csv` contains the canonical NOAA-Spec cleaned output with sentinel values normalized to nulls and quality-code semantics preserved.

## Run The Canonical Contract

The canonical dataset defines the reproducible interpretation contract. In that public canonical CSV, the station identifier remains `STATION`, matching the bundled fixture and CLI output. Optional `--view` outputs are narrower domain-specific datasets for usability and do not modify the underlying contract.

For a first inspection path, many users begin with a smaller derived view:

```bash
noaa-spec clean reproducibility/minimal/station_raw.csv /tmp/station_metadata.csv --view metadata
```

The canonical CSV is the full loss-preserving contract and is intentionally wide. Optional views are narrower usability-oriented datasets derived from that canonical output, so you can orient yourself quickly and then expand into the full canonical columns as needed.

## Optional Derived Views

Other supported views:

- `metadata`
- `wind`
- `precipitation`
- `clouds_visibility`
- `pressure_temperature`
- `remarks`

The `metadata` view contains station/time context and identifying metadata rather than cleaned meteorological measurements. For compatibility, `core` and `core_meteorology` remain accepted aliases for `metadata`.

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

## Further Reading

For a column-level explanation of the cleaned output, see [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md).
For a worked example showing what a user gains from the canonical layer, see [docs/examples/CANONICAL_WALKTHROUGH.md](docs/examples/CANONICAL_WALKTHROUGH.md).

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

The tracked fixture is also used for checksum-backed reproducibility verification:

- Raw input: [reproducibility/minimal/station_raw.csv](reproducibility/minimal/station_raw.csv)
- Expected cleaned output: [reproducibility/minimal/station_cleaned_expected.csv](reproducibility/minimal/station_cleaned_expected.csv)
- Expected cleaned SHA256: `b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597`

The included fixture is intentionally minimal (5 rows) and serves as a deterministic reproducibility proof.

For the complete verification workflow, Docker clean-environment path, and explicit reproducibility boundary, see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Docs

- Reproducibility: [REPRODUCIBILITY.md](REPRODUCIBILITY.md)
- Output guide: [docs/UNDERSTANDING_OUTPUT.md](docs/UNDERSTANDING_OUTPUT.md)
- Worked example: [docs/examples/CANONICAL_WALKTHROUGH.md](docs/examples/CANONICAL_WALKTHROUGH.md)
