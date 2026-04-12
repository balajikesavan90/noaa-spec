# NOAA-Spec

NOAA-Spec is a deterministic cleaning layer for NOAA ISD / Global Hourly observations. It provides one reviewer-facing workflow: run `noaa-spec clean` on a raw NOAA-style CSV and get a reproducible cleaned CSV with sentinel-coded values normalized to nulls, NOAA quality-code semantics preserved, and deterministic row/order serialization.

This tool provides a consistent and reproducible interpretation of NOAA ISD CSV fields, rather than asserting a single authoritative canonical schema for all possible NOAA data.

## What This Does

- Cleans raw NOAA ISD / Global Hourly CSV rows into a reproducible observation-level CSV.
- Converts documented sentinel-coded measurements such as `+9999,9` into null measurement values.
- Preserves NOAA quality codes in explicit columns such as `temperature_quality_code`.
- Emits deterministic CSV output using stable sorting, UTF-8 encoding, LF line endings, and empty-string null serialization.
- Includes tracked fixtures so reviewers can rerun the same input and compare the exact expected checksum.

NOAA-Spec does not download NOAA data or orchestrate multi-station batch processing. The submitted software surface is the `noaa-spec clean` CLI.

## First Run

Use Docker for a clean reviewer run:

```bash
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Expected result:

```text
PASS: reproducibility verification succeeded.
SHA256: b48aba1b8a304451dc3874b963d76275bf79ad68c6f28d9190e0e636f2887597
```

The Docker path installs the package, runs `noaa-spec clean` against the tracked fixture, and checks that the generated CSV matches the expected SHA256.

After running the fixture, open:

- `reproducibility/minimal/station_raw.csv` for the raw NOAA-style input.
- `reproducibility/minimal/station_cleaned_expected.csv` for the expected cleaned output.
- `docs/schema.md` for the cleaned CSV schema contract and naming conventions.
- `docs/rule_provenance.md` for representative rule-to-source traceability.

## Local Install

Python 3.11 or 3.12 is required.

```bash
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

If the console script is not on `PATH`, use:

```bash
python -m noaa_spec.cli clean reproducibility/minimal/station_raw.csv /tmp/station_cleaned.csv
```

On Windows PowerShell, the equivalent command after activation is:

```powershell
noaa-spec clean reproducibility/minimal/station_raw.csv $env:TEMP\station_cleaned.csv
Get-FileHash $env:TEMP\station_cleaned.csv -Algorithm SHA256
```

## Minimal Example

The primary fixture is tracked at `reproducibility/minimal/station_raw.csv`.

Raw input excerpt:

```text
DATE                 TMP      DEW      VIS
2000-01-10T06:00:00  +0180,1  +0100,1  010000,1,N,1
2000-03-17T09:00:00  +9999,9  +9999,9  999999,9,N,1
```

Cleaned output excerpt:

```text
DATE                 temperature_c  temperature_quality_code  dew_point_c  visibility_m  TMP__qc_reason
2000-01-10T06:00:00  18.0           1                         10.0         10000.0
2000-03-17T09:00:00                 9                                      SENTINEL_MISSING
```

The raw token `TMP=+9999,9` becomes a null `temperature_c`, while the NOAA quality code `9` remains available in `temperature_quality_code`.

The full fixture output is intentionally wider than this excerpt. NOAA composite fields such as `WND`, `VIS`, `TMP`, `AA1`, and `GA1` can each expand into decoded measurement columns, preserved NOAA quality-code columns, and `__qc_*` validation sidecars. See [docs/schema.md](docs/schema.md) for the schema contract.

## Why Not a Simple Script?

Loading the raw CSV with pandas is useful, but it does not by itself interpret NOAA ISD encoded fields. NOAA-Spec exists to make a small set of NOAA-specific cleaning decisions explicit and repeatable.

### Naive TMP parsing

`TMP=+9999,9` is parsed as numeric and becomes `999.9` or `9999`.

Problem:
- The sentinel is interpreted as a real value.
- The quality code is lost or treated as a measurement suffix.
- The missingness meaning is destroyed.

NOAA-Spec behavior:
- `temperature_c` becomes null.
- `temperature_quality_code=9` is preserved.
- `TMP__qc_reason=SENTINEL_MISSING` is emitted.

### Naive VIS parsing

`VIS=999999,9,N,1` is split as ordinary comma-separated values.

Problem:
- The visibility sentinel can become a real 999999 m distance.
- The distance quality code can be dropped.
- The variability fields can be separated from the measurement they qualify.

NOAA-Spec behavior:
- `visibility_m` becomes null.
- `visibility_quality_code=9` is preserved.
- Visibility variability and variability quality remain explicit columns.

NOAA-Spec does not replace downstream analysis. It gives reviewers and researchers a deterministic cleaned starting point with nulls, quality codes, and validation sidecars visible.

## Fixture Coverage

The tracked reproducibility fixtures are small by design:

- `reproducibility/minimal/`: 5 raw rows, used by the Docker and local checksum path.
- `reproducibility/minimal_second/`: 8 raw rows, covering additional precipitation, cloud, past-weather, extreme-temperature, and present-weather fields.

These fixtures prove deterministic behavior for committed input/output pairs. Broader correctness is covered by the automated tests in `tests/`, especially cleaning, QC, deterministic I/O, CLI behavior, field parsing, and fixture reproduction tests.

## Run Tests

```bash
python -m pip install -e .
python -m pip install pytest
python -m pytest tests -v
```

## Repository Map

- `docs/schema.md`: reviewer-facing cleaned CSV schema contract.
- `docs/rule_provenance.md`: representative rule provenance and source-doc pointers.
- `src/noaa_spec/cleaning.py`: NOAA field interpretation and cleaning logic.
- `src/noaa_spec/constants.py`: encoded field rules, sentinels, and QC definitions.
- `src/noaa_spec/deterministic_io.py`: deterministic CSV writer.
- `src/noaa_spec/cli.py`: public `noaa-spec clean` entry point.
- `reproducibility/`: tracked raw and expected cleaned fixtures.
- `tests/`: reviewer-relevant regression tests.
- `paper/`: JOSS manuscript source.

See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) for the exact checksum workflow.
