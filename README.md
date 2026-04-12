# NOAA-Spec

NOAA-Spec is a deterministic cleaning layer for NOAA ISD / Global Hourly CSV observations. Its public JOSS-facing workflow is:

```bash
noaa-spec clean INPUT.csv OUTPUT.csv
```

The command writes an observation-level cleaned CSV with documented NOAA sentinels normalized to empty null cells, NOAA quality codes preserved in explicit columns, and deterministic row/order serialization. NOAA-Spec does not download NOAA data, orchestrate station batches, produce releases, or run analyses.

## Reviewer Path

Use the repository-defined, tested Docker reviewer environment:

```bash
docker build -f Dockerfile -t noaa-spec-review .
docker run --rm noaa-spec-review bash scripts/verify_reproducibility.sh
```

Expected result: one `PASS` line for each tracked `station_cleaned_expected.csv`
entry in `reproducibility/checksums.sha256`, followed by:

```text
PASS: reproducibility verification succeeded.
Output directory: /tmp/noaa-spec-reproducibility
```

The canonical checksum list is `reproducibility/checksums.sha256`.

The Dockerfile uses the floating `python:3.12-slim` base image and upgrades bootstrap packaging tools during build. Treat it as a tested reviewer environment, not an immutable archived runtime.

## Fully Traceable Example

The strongest provenance example is:

- Raw input: `reproducibility/real_provenance_example/station_raw.csv`
- Expected cleaned output: `reproducibility/real_provenance_example/station_cleaned_expected.csv`
- Checksums: `reproducibility/checksums.sha256`
- Provenance note: `reproducibility/REAL_PROVENANCE_EXAMPLE.md`

It uses the first five data rows from the NOAA/NCEI Global Hourly CSV for station `03041099999`:

```text
https://www.ncei.noaa.gov/data/global-hourly/access/2024/03041099999.csv
```

Run it directly after installing the package:

```bash
noaa-spec clean \
  reproducibility/real_provenance_example/station_raw.csv \
  /tmp/noaa-spec-real-provenance.csv
sha256sum /tmp/noaa-spec-real-provenance.csv
```

Compare the generated checksum with the matching
`reproducibility/real_provenance_example/station_cleaned_expected.csv` entry in
`reproducibility/checksums.sha256`.

Expected output snapshot for the first five rows:

| STATION | DATE | temperature_c | temperature_quality_code | visibility_m | visibility_quality_code | wind_speed_ms | wind_speed_quality_code |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 03041099999 | 2024-01-01T00:00:00 | -1.8 | 1 |  | 9.0 |  | 9.0 |
| 03041099999 | 2024-01-01T01:00:00 | -1.6 | 1 |  | 9.0 |  | 9.0 |
| 03041099999 | 2024-01-01T02:00:00 | -1.5 | 1 |  | 9.0 |  | 9.0 |
| 03041099999 | 2024-01-01T03:00:00 | -1.6 | 1 |  | 9.0 |  | 9.0 |
| 03041099999 | 2024-01-01T04:00:00 | -1.8 | 1 |  | 9.0 |  | 9.0 |

## First Output: What To Look At

Start with decoded measurement columns and their NOAA quality-code columns. Ignore `__qc_*` sidecars on the first pass unless a decoded value is empty or surprising.

| Column | What to check |
| --- | --- |
| `STATION`, `DATE` | Source station and observation timestamp. |
| `temperature_c` | Decoded air temperature; sentinels become null. |
| `temperature_quality_code` | NOAA QC code preserved from `TMP`. |
| `dew_point_c` | Decoded dew point temperature. |
| `visibility_m` | Decoded visibility; `999999` becomes null. |
| `visibility_quality_code` | NOAA QC code preserved from `VIS`. |
| `wind_speed_ms` | Decoded wind speed from `WND`. |
| `wind_speed_quality_code` | NOAA QC code preserved for wind speed. |
| `sea_level_pressure_hpa` | Decoded sea-level pressure; `99999` becomes null. |

For a slightly fuller guide, see [docs/first_output_guide.md](docs/first_output_guide.md). For the field contract, see [docs/supported_fields.md](docs/supported_fields.md).

## Why Not Pandas?

Pandas can load the CSV, but it does not know NOAA sentinel semantics. A raw visibility token such as:

```text
VIS=999999,9,N,1
```

can be naively split into a numeric value of `999999`, which is not a real visibility distance. NOAA-Spec emits an empty `visibility_m`, preserves `visibility_quality_code=9`, and records the parser reason in `VIS__part1__qc_reason`.

Run the minimal comparison:

```bash
python examples/pandas_vs_noaa_spec.py
```

## Local Install

Python 3.11 or 3.12 is required.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .
```

Use `python3.11` instead of `python3.12` if that is your supported local interpreter.

If the console script is not on `PATH`, use:

```bash
python -m noaa_spec.cli clean INPUT.csv OUTPUT.csv
```

## Reproducibility Fixtures

The tracked fixtures are small by design:

- `reproducibility/real_provenance_example/`: five rows from a recorded NOAA/NCEI Global Hourly source URL; this is the strongest provenance example.
- `reproducibility/minimal/`: five raw rows for the compact reviewer fixture.
- `reproducibility/minimal_second/`: eight raw rows covering additional encoded fields.
- `reproducibility/station_03041099999_aonach_mor/`, `reproducibility/station_01116099999_stokka/`, and `reproducibility/station_94368099999_hamilton_island/`: four-row curated station slices. Their exact upstream retrieval metadata was not retained.

These fixtures prove deterministic behavior for committed input/output pairs. They do not claim exhaustive NOAA coverage. See [REPRODUCIBILITY.md](REPRODUCIBILITY.md) and [reproducibility/FIXTURE_PROVENANCE.md](reproducibility/FIXTURE_PROVENANCE.md).

## Optional, Outside JOSS Core

`noaa-spec split-domains` can split an already-cleaned CSV into convenience domain CSVs:

```bash
noaa-spec split-domains CLEANED.csv OUTPUT_DIR --prefix example
```

This command is optional. It is not part of the core JOSS contribution, not part of the reviewer checksum workflow, and not part of the primary reproducibility claim. Manifest files written by this optional command are runtime support artifacts for that optional workflow only.

## Run Tests

```bash
python -m pip install -e .
python -m pip install pytest
python -m pytest tests -v
```

## Repository Map

- `src/noaa_spec/cli.py`: public `noaa-spec clean` entry point.
- `src/noaa_spec/cleaning.py`: NOAA field interpretation and cleaning logic.
- `src/noaa_spec/constants.py`: encoded field rules, sentinels, and QC definitions.
- `src/noaa_spec/deterministic_io.py`: deterministic CSV writer.
- `docs/first_output_guide.md`: quick guide for reading the first cleaned CSV.
- `docs/supported_fields.md`: supported cleaned-output field registry.
- `docs/schema.md`: cleaned CSV interpretation and naming conventions.
- `docs/rule_provenance.md`: rule-family provenance and source-doc pointers.
- `reproducibility/`: tracked raw and expected cleaned fixtures.
- `spec_sources/`: NOAA ISD documentation material used for repository reference.
- `paper/`: JOSS manuscript source.
