# noaa-climate-data

Python pipeline to pull, clean, and aggregate climate data from NOAA's
[Integrated Surface Database (ISD)](https://www.ncei.noaa.gov/products/land-based-station/integrated-surface-database)
Global Hourly archive.

## What's New (Since February 19, 2026)

- **Specification Compliance System**: Auto-generated spec coverage tracking across 3,583+ NOAA ISD rules with deterministic rule matching
- **Domain Enforcement**: Categorical field validation against spec-defined allowed values and patterns
- **Massive Test Expansion**: Test count increased from ~308 to **3,800+** with three new comprehensive test suites
- **Validation Documentation**: Two new design docs ([PIPELINE_DESIGN_RATIONALE.md](docs/PIPELINE_DESIGN_RATIONALE.md), [PIPELINE_VALIDATION_PLAN.md](docs/PIPELINE_VALIDATION_PLAN.md))
- **Suspicious Coverage Monitoring**: CI workflow that detects test/code alignment issues
- **Enhanced Field Rules**: 131 field families now defined in constants.py with 1,105+ lines of new spec-based rules
- **Enhanced QC Signals**: Improved handling of malformed tokens, sentinel detection, and boundary conditions

See [Specification Compliance & Validation](#specification-compliance--validation) for details.

---

## Overview

This project replaces the legacy R scripts with a Python pipeline that:

1. **Discovers** the NOAA Global Hourly file list and year coverage counts.
2. **Builds** station metadata (location IDs) for all stations in the year-count list.
3. **Downloads** all available metrics for a station across multiple years.
4. **Cleans** comma-encoded ISD fields — applying per-field sentinel detection, scale
   factors, and quality-flag filtering via a declarative `FIELD_RULES` registry.
5. **Aggregates** numeric metrics to monthly and yearly summaries using
   field-appropriate functions (mean, min, max) while excluding categorical codes
   and quality flags from aggregation.

## Quick start

### Requirements

- Python ≥ 3.12
- [Poetry](https://python-poetry.org/) for dependency management

### Install

```bash
poetry install
```

### Run tests

```bash
poetry run python -m pytest tests/ -v
```

Run specific test suites:

```bash
# Core cleaning logic (1,955+ tests)
poetry run pytest tests/test_cleaning.py -v

# QC signal handling (803 tests)
poetry run pytest tests/test_qc_comprehensive.py -v

# Spec coverage generator (874 tests)
poetry run pytest tests/test_spec_coverage_generator.py -v

# Aggregation logic (19 tests)
poetry run pytest tests/test_aggregation.py -v

# Integration tests (165 tests)
poetry run pytest tests/test_integration.py -v
```

See [Enhanced Test Suite](#enhanced-test-suite) below for detailed test coverage.

## Commands

### Build the file list and coverage counts

```bash
poetry run python -m noaa_climate_data.cli file-list \
  --start-year <START_YEAR> \
  --end-year <END_YEAR> \
  --sleep-seconds 0.5 \
  --retries 3 \
  --backoff-base 0.5 \
  --backoff-max 8
```

Writes `noaa_file_index/YYYYMMDD/DataFileList.csv` and
`noaa_file_index/YYYYMMDD/DataFileList_YEARCOUNT.csv` (date is UTC).

### Build station metadata (location IDs)

```bash
poetry run python -m noaa_climate_data.cli location-ids \
  --start-year <START_YEAR> \
  --end-year <END_YEAR> \
  --sleep-seconds 0.5 \
  --retries 3 \
  --backoff-base 0.5 \
  --backoff-max 8
```

Batching/resume options:

```bash
poetry run python -m noaa_climate_data.cli location-ids \
  --start-year <START_YEAR> \
  --end-year <END_YEAR> \
  --max-locations 100 \
  --checkpoint-every 100 \
  --checkpoint-dir noaa_file_index/YYYYMMDD \
  --sleep-seconds 0.5
```

- Resume is enabled by default (loads existing `Stations.csv` and skips already-processed stations).
- Use `--no-resume` to force a fresh run.
- Use `--start-index` to skip the first N rows in `DataFileList_YEARCOUNT.csv`.
- `--max-locations` limits how many new stations to fetch per run.
- `--checkpoint-every` writes periodic copies of `Stations.csv` (default 100).
- `--checkpoint-dir` controls where checkpoint copies are written.

Reads from the latest `noaa_file_index/YYYYMMDD/` folder and writes
`noaa_file_index/YYYYMMDD/Stations.csv`.

### Download, clean, and aggregate a station

```bash
poetry run python -m noaa_climate_data.cli process-location 01001099999.csv \
  --start-year <START_YEAR> \
  --end-year <END_YEAR> \
  --sleep-seconds 0.5 \
  --output-dir output
```

Optional: add imperial/derived unit columns alongside metric outputs:

```bash
poetry run python -m noaa_climate_data.cli process-location 01001099999.csv \
  --add-unit-conversions \
  --output-dir output
```

Pick an aggregation strategy:

```bash
poetry run python -m noaa_climate_data.cli process-location 01001099999.csv \
  --aggregation-strategy hour_day_month_year \
  --min-hours-per-day 18 \
  --min-days-per-month 20 \
  --min-months-per-year 12 \
  --output-dir output
```

Fixed-hour example:

```bash
poetry run python -m noaa_climate_data.cli process-location 01001099999.csv \
  --aggregation-strategy fixed_hour \
  --fixed-hour 12 \
  --output-dir output
```

Output files per station:

| File | Description |
|------|-------------|
| `LocationData_Raw.csv` | Raw NOAA CSV concatenated across years |
| `LocationData_Cleaned.csv` | After sentinel removal, scaling, quality filtering |
| `LocationData_Hourly.csv` | Hourly output from the chosen aggregation strategy (best/fixed hour keeps only that hour; other strategies keep hours belonging to complete days/months/years) |
| `LocationData_Monthly.csv` | Aggregated to month level |
| `LocationData_Yearly.csv` | Aggregated to year level |

### Pick a random station and pull raw parquet

`Stations.csv` now includes status columns that track progress:

| Column | Meaning |
|--------|---------|
| `raw_data_pulled` | Raw NOAA parquet was written for the station |
| `data_cleaned` | Cleaned parquet was written for the station |
| `data_aggregated` | Aggregated parquet outputs were written for the station |

Pull a random station that has not yet downloaded raw data:

```bash
poetry run python -m noaa_climate_data.cli pick-location \
  --start-year <START_YEAR> \
  --end-year <END_YEAR> \
  --sleep-seconds 0.5 \
  --output-dir output
```

This writes `LocationData_Raw.parquet` under `output/<station>/` and marks
`raw_data_pulled=True` in the latest `noaa_file_index/YYYYMMDD/Stations.csv`.

### Clean a raw parquet

```bash
poetry run python -m noaa_climate_data.cli clean-parquet output/01001099999/LocationData_Raw.parquet \
  --file-name 01001099999.csv
```

This writes `LocationData_Cleaned.parquet` alongside the raw parquet and marks
`data_cleaned=True` in the latest `noaa_file_index/YYYYMMDD/Stations.csv`.

### Convert a PDF to deterministic markdown

```bash
poetry run python -m noaa_climate_data.cli pdf-to-markdown path/to/input.pdf
```

Optional output path and formatting:

```bash
poetry run python -m noaa_climate_data.cli pdf-to-markdown path/to/input.pdf \
  --output-md path/to/output.md \
  --no-page-headers
```

This command uses page-ordered extraction with stable normalization (Unicode NFKC,
line ending normalization, trimmed trailing whitespace, and collapsed blank-line runs)
to keep output deterministic across repeated runs in the same environment.

---

## Project structure

```
src/noaa_climate_data/
├── cli.py          # CLI entry point (file-list, location-ids, process-location)
├── constants.py    # FIELD_RULES registry, quality flags, column helpers
├── cleaning.py     # Comma-encoded field parsing, sentinel/scale/quality/domain logic
├── noaa_client.py  # HTTP access to NOAA archive (listing, download, metadata)
└── pipeline.py     # End-to-end orchestration, time extraction, aggregation

tests/
├── test_cleaning.py                      # Unit tests for cleaning logic (1,955+ tests)
├── test_aggregation.py                   # Unit tests for aggregation logic
├── test_integration.py                   # Integration tests against real station outputs
├── test_qc_comprehensive.py              # QC signal comprehensive tests (803 tests)
├── test_spec_coverage_generator.py       # Spec coverage system tests (874 tests)
└── test_suspicious_coverage_integrity.py # Suspicious coverage validation (84 tests)

docs/
├── PIPELINE_DESIGN_RATIONALE.md      # Architecture & spec-compliance approach
├── PIPELINE_VALIDATION_PLAN.md       # Validation KPIs and mandatory test tracks
└── validation_artifacts/
    └── suspicious_coverage/
        └── suspicious_summary.md     # Latest suspicious coverage report

tools/
└── spec_coverage/
    ├── generate_spec_coverage.py         # Spec rule extraction & coverage tracking
    └── export_suspicious_summary.py      # Suspicious coverage report generator
```

---

## QC Signals & Data Quality

Every numeric field in cleaned output now includes **QC signal columns** indicating data quality:

- `{FIELD}__qc_pass` (Boolean) – Validation checks passed (range, quality flag, sentinel)
- `{FIELD}__qc_status` (String) – "PASS" or "INVALID"
- `{FIELD}__qc_reason` (String or None) – Reason for failure (e.g., "OUT_OF_RANGE", "BAD_QUALITY_CODE", "SENTINEL_MISSING")

Plus row-level summaries:
- `row_has_any_usable_metric` (Boolean) – At least one metric passed QC
- `usable_metric_count` (Integer) – Count of passing metrics
- `usable_metric_fraction` (Float [0, 1]) – Fraction of metrics that passed

**Current scope**: OC1 (wind), MA1 (pressure), GE1/GF1/GG (cloud), GH1 (solar), KA/KB (temperature)

**Example usage**:
```python
from noaa_climate_data.cleaning import clean_noaa_dataframe
df = clean_noaa_dataframe(df_raw)
df_quality = df[df["OC1__qc_pass"] == True]  # Keep valid wind gust only
high_quality = df[df["usable_metric_fraction"] >= 0.75]  # ≥75% metrics passed
```

For detailed documentation, see [QC_SIGNALS_ARCHITECTURE.md](QC_SIGNALS_ARCHITECTURE.md).

---

## Data pipeline details

### 1. Data acquisition

The pipeline targets NOAA's Global Hourly CSV archive at the base URL defined in
[src/noaa_climate_data/constants.py](src/noaa_climate_data/constants.py).

**File list discovery**

- `get_years()` scrapes the NOAA access page, keeping only 4‑digit directory names.
- `get_file_list_for_year(year)` scrapes each year directory and retains only `.csv` entries.
- `build_file_list(years)` produces `YEAR` + `FileName` rows for all available year directories.

**Station coverage selection**

- `count_years_per_file(...)` filters the file list by the requested year range and counts how
  many years each file appears.
- `build_location_ids(...)` includes all stations in the year-count list (no coverage filter).
- For each included file, metadata is pulled from the first available year; fallback years are
  searched if the primary metadata year is missing.

**Download for a station**

- `download_location_data(file_name, years)` attempts `pandas.read_csv(url)` for each year.
- A year is silently skipped if the read fails or returns an empty frame.
- Each non‑empty year frame is tagged with a `YEAR` column and concatenated.

### 2. Cleaning

Cleaning is performed by `clean_noaa_dataframe(...)` in
[src/noaa_climate_data/cleaning.py](src/noaa_climate_data/cleaning.py), driven by
the declarative `FIELD_RULES` registry in
[src/noaa_climate_data/constants.py](src/noaa_climate_data/constants.py).

#### 2a. Field parsing

- Only object/string columns are candidates for expansion.
- A column is parsed if any sampled value contains a comma.
- Values are split on commas into parts (e.g., `value,quality` or longer compound fields).

#### 2b. Column expansion

- **2-part fields** (e.g. TMP, DEW, SLP, OC1, SA1) produce:
  - `<column>__value` — numeric after sentinel removal, scaling, and quality filtering
  - `<column>__quality` — the quality flag character
- **Multi-part fields** (e.g. WND, CIG, VIS, MA1, MD1) produce:
  - `<column>__partN` for each part — numeric if parseable, otherwise raw text
  - `<column>__quality` only when the registry defines a single shared quality part
  - When parts each carry their own quality, those quality parts stay as their own
    `__partN` columns (and are renamed via the friendly map instead of being
    duplicated as a shared `__quality` column)
- The original raw column is preserved by default (`keep_raw=True`).

#### 2b.1 Human-readable column names

Expanded columns are renamed using the friendly map in
[src/noaa_climate_data/constants.py](src/noaa_climate_data/constants.py). Key examples:

| Raw column | Friendly name |
|------------|---------------|
| `WND__part1` | `wind_direction_deg` |
| `WND__part4` | `wind_speed_ms` |
| `CIG__part1` | `ceiling_height_m` |
| `VIS__part1` | `visibility_m` |
| `TMP__value` | `temperature_c` |
| `DEW__value` | `dew_point_c` |
| `OC1__value` | `wind_gust_ms` |
| `MA1__part1` | `altimeter_setting_hpa` |
| `UA1__part1` | `wave_method_code` |
| `UA1__part2` | `wave_period_seconds` |
| `UA1__part3` | `wave_height_m` |
| `UA1__part5` | `sea_state_code` |
| `UG1__part1` | `swell_period_seconds` |
| `UG1__part2` | `swell_height_m` |
| `UG1__part3` | `swell_direction_deg` |
| `MV1__part1` | `present_weather_vicinity_code_1` |
| `MV1__part2` | `present_weather_vicinity_quality_code_1` |

#### 2b.2 Derived parsing flags and remark fields

- `WND__direction_variable` is `True` when WND direction is `999` and the wind type code is `V` (variable).
- `REM` (remarks) is split into `REM__type` and `REM__text` when the value begins with a known remark prefix.
- `QNN` (original observation data) is parsed into `QNN__elements`, `QNN__source_flags`, and `QNN__data_values`.

#### 2c. Missing-value sentinel detection

Each field declares its own sentinel values in `FIELD_RULES`. The pipeline:

1. Strips leading zeros from raw values (e.g. `009999` → `9999`) before comparison.
2. Checks the sentinel **before** attempting numeric conversion, so values like VIS `9999`
   are correctly caught even though they parse as valid numbers.
3. Replaces detected sentinels with `None` (NaN in pandas).

| Field | Sentinel values | Meaning |
|-------|----------------|---------|
| WND direction | `999` | Missing wind direction |
| WND speed | `9999` | Missing wind speed |
| CIG height | `99999` | Missing ceiling height |
| VIS distance | `999999` | Missing visibility |
| TMP, DEW | `9999` | Missing temperature |
| SLP | `99999` | Missing sea-level pressure |
| OC1 gust | `9999` | Missing wind gust |
| MA1 altimeter/pressure | `99999` | Missing pressure |
| KA\* period/temperature | `999`, `9999` | Missing extreme temp |
| MD1 Δp | `999`, `+999` | Missing pressure change |
| SA1 SST | `999` | Missing sea-surface temperature |
| GE1 convective cloud code | `9` | Missing convective cloud code |
| GE1 vertical datum | `999999` | Missing vertical datum |
| UA1 wave period | `99` | Missing wave period (seconds) |
| UA1 wave height | `999` | Missing wave height |
| UG1 swell period | `99` | Missing swell period (seconds) |
| UG1 swell height | `999` | Missing swell height |
| UG1 swell direction | `999` | Missing swell direction |

Fields without a declared rule fall back to generic all-9s detection.

#### 2d. Scale factors

Scale factors are applied after sentinel removal:

| Field | Part(s) | Scale | Output unit |
|-------|---------|-------|-------------|
| TMP | value | ÷10 | °C |
| DEW | value | ÷10 | °C |
| SLP | value | ÷10 | hPa |
| WND | part4 (speed) | ÷10 | m/s |
| OC1 | value (gust) | ÷10 | m/s |
| MA1 | part1 (altimeter), part3 (stn pressure) | ÷10 | hPa |
| KA\* | part1 (period), part3 (temperature) | ÷10 | hours, °C |
| MD1 | part3 (3hr Δp), part5 (24hr Δp) | ÷10 | hPa |
| OD\* | part4 (speed) | ÷10 | m/s |
| SA1 | value (SST) | ÷10 | °C |
| UA1 | part3 (wave height) | ÷10 | m |
| UG1 | part2 (swell height) | ÷10 | m |

#### 2e. Quality-flag filtering

- Allowed quality flags (`QUALITY_FLAGS`): `{0, 1, 2, 3, 4, 5, 6, 7, 9, A, C, I, M, P, R, U}`.
- Some sections (e.g., UA1/UG1 marine groups, MV/OD wind) apply narrower per-field quality limits per ISD specs.
- Erroneous quality codes (`3`, `7`) are retained in `LocationData_Cleaned.csv` for researcher transparency,
  but those values are excluded during monthly/yearly aggregation.
- Each value part in `FIELD_RULES` declares which quality part governs it via `quality_part`.
- If the governing quality flag is **not** in the allowed set, only that specific value is set
  to `None` — other parts in the same field are preserved.
- Example: WND direction has `quality_part=2`, WND speed has `quality_part=5`. A bad direction
  quality nulls direction but preserves speed, and vice versa.

#### 2f. Domain enforcement

**New as of February 2026**: Each field part can declare an `allowed_values` set or `allowed_pattern` regex that constrains categorical codes to spec-defined domains:

- **allowed_values**: Explicit set of permitted codes (e.g., WND type ∈ `{A, B, C, H, N, R, Q, T, V, 9}`, MW1 weather ∈ `{01-99}`)
- **allowed_pattern**: Regex pattern for more complex constraints (e.g., present weather codes `^\d{2}$`)
- Values outside the allowed domain are set to `None` and flagged in QC signals
- Domain rules are extracted from the NOAA ISD specification and tracked in the spec coverage system

Domain enforcement ensures that only spec-valid categorical codes appear in cleaned output, preventing data corruption from malformed or out-of-spec observations.

### 3. Aggregation

Aggregation happens in `process_location(...)` in
[src/noaa_climate_data/pipeline.py](src/noaa_climate_data/pipeline.py).

This monthly/yearly aggregation is a project-specific analysis layer. NOAA ISD
does not define these summary products, so treat them as derived outputs rather
than source-of-record observations.

#### 3a. Time extraction

- `DATE` is parsed as UTC; rows with invalid dates are dropped.
- Derived columns: `Year`, `MonthNum`, `Day` (date only), `Hour`.

#### 3b. Field-appropriate aggregation functions

Each field declares its preferred aggregation function in `FIELD_RULES`. The pipeline
builds a per-column `agg_spec` for `groupby().agg()`:

| Function | Fields | Rationale |
|----------|--------|-----------|
| **mean** | TMP, DEW, SLP, WND speed, MA1, KA\*, MD1, SA1, GA\* | Central tendency for continuous measurements |
| **circular_mean** | WND direction | Wrap-aware mean for angular degrees |
| **max** | OC1 (wind gust) | Peak gust is the meaningful aggregate |
| **min** | VIS (visibility) | Worst visibility is climatologically significant |
| **sum** | Precipitation/snow totals (AA\*, AL\*, AO\*, AP\*) | Accumulate totals over the period |
| **mode** | Columns explicitly tagged with `agg="mode"` | Most-common categorical value when configured |
| **drop** | WND type code, CIG determination/CAVOK, VIS variability, MW\* weather codes/quality, AY\* condition/period codes/quality, MD1 tendency code, GE1 categorical codes, all `*__quality` columns | Categorical codes and quality flags are observation-level metadata |

#### 3c. Aggregation strategies

| Strategy | Description |
|----------|-------------|
| `best_hour` (default) | Choose the hour with the most unique days, keep only those rows, then aggregate to monthly/yearly |
| `fixed_hour` | Use a specific UTC hour (e.g. 12), then aggregate |
| `hour_day_month_year` | Aggregate hour → day → month → year |
| `weighted_hours` | Require ≥N hours/day, weight by hour counts |
| `daily_min_max_mean` | Compute daily min/max/mean, then aggregate those |

#### 3d. Completeness filters

- A **month** is complete if it has ≥ 20 unique days (configurable via `--min-days-per-month`).
- A **year** is complete if it has all 12 months present after the month filter
  (configurable via `--min-months-per-year`).
- These filters are applied before monthly/yearly aggregation to ensure statistical reliability.

---

## Field reference

| Field | Parts | Key value part(s) | Scale | Sentinel(s) | Quality part(s) | Agg | Type |
|-------|-------|-------------------|-------|-------------|-----------------|-----|------|
| WND | 5 | 1=direction, 4=speed | 1, 0.1 | 999, 9999 | 2, 5 | circular_mean/mean | numeric |
| CIG | 4 | 1=height | 1 | 99999 | 2 | mean | numeric |
| VIS | 4 | 1=distance | 1 | 999999 | 2 | min | numeric |
| TMP | 2 | 1=temperature | 0.1 | 9999 | 2 | mean | numeric |
| DEW | 2 | 1=dew point | 0.1 | 9999 | 2 | mean | numeric |
| SLP | 2 | 1=pressure | 0.1 | 99999 | 2 | mean | numeric |
| OC1 | 2 | 1=gust speed | 0.1 | 9999 | 2 | max | numeric |
| MA1 | 4 | 1=altimeter, 3=stn press | 0.1, 0.1 | 99999, 99999 | 2, 4 | mean | numeric |
| KA\* | 4 | 1=period, 2=code, 3=temperature | 0.1, 1, 0.1 | 999, 9, 9999 | 4 | mean/drop | mixed |
| MD1 | 6 | 1=tendency, 3=3hr Δp, 5=24hr Δp | —, 0.1, 0.1 | 9, 999, +999 | 2, 4, 6 | drop/mean | mixed |
| OA\* | 4 | 1=type, 2=period, 3=speed | —, 1, 0.1 | 9, 99, 9999 | 4 | drop/mean | mixed |
| OD\* | 5 | 3=direction, 4=speed | 1, 0.1 | 999, 9999 | 5 | circular_mean/mean | numeric |
| GA\* | 6 | 1=coverage, 3=base height | 1, 1 | 99, 99999 | 2, 4, 6 | mean | mixed |
| GF1 | 13 | 1=total cov, 8=base ht | 1, 1 | 99, 99999 | 3, 5, 7, 9, 11, 13 | mean | mixed |
| MW\* | 2 | 1=weather code | — | — | 2 | drop | categorical |
| MV\* | 2 | 1=vicinity weather code | — | 99 | 2 | drop | categorical |
| AY\* | 4 | 1=condition, 3=period | —, 1 | —, 99 | 2, 4 | drop | categorical |
| AT\* | 4 | 1=source, 2=type, 3=abbr | — | — | 4 | drop | categorical |
| AU\* | 7 | 1=intensity, 2=descriptor, 3=precip, 4=obscuration, 5=other, 6=combo | — | 9, 99 | 7 | drop | categorical |
| CB\* | 4 | 1=period, 2=secondary depth | 1, 0.1 | 99, 99999 | 3 | mean/drop | mixed |
| CF\* | 3 | 1=fan speed | 0.1 | 9999 | 2 | mean/drop | mixed |
| CG\* | 3 | 1=primary depth | 0.1 | 99999 | 2 | mean/drop | mixed |
| CH\* | 7 | 1=period, 2=temp, 5=RH | 1, 0.1 | 99, 9999 | 3, 6 | mean/drop | mixed |
| CI1 | 12 | 1=min temp, 4=max temp, 7=temp std, 10=RH std | 0.1 | 9999, 99999 | 2, 5, 8, 11 | mean/drop | mixed |
| CN1 | 9 | 1=avg volt, 4=full load, 7=datalogger | 0.1 | 9999 | 2, 5, 8 | mean/drop | mixed |
| CN2 | 9 | 1=panel temp, 4=inlet max, 7=door minutes | 0.1 | 9999, 99 | 2, 5, 8 | mean/drop | mixed |
| CN3 | 6 | 1=ref resistance, 4=signature | 0.1 | 999999 | 2, 5 | mean/drop | mixed |
| CN4 | 12 | 1=heater flag, 4=door flag, 7/10=tx power | 0.1 | 9, 9999, 999 | 2, 5, 8, 11 | mean/drop | mixed |
| CO1 | 2 | 1=climate division, 2=UTC offset | 1 | 99 | — | drop | categorical |
| CO\* | 2 | 1=element id, 2=time offset | 1, 0.1 | 999, 9999 | — | drop/mean | mixed |
| CR1 | 3 | 1=datalogger version | 0.001 | 99999 | 2 | mean/drop | mixed |
| CT\* | 3 | 1=subhourly temp | 0.1 | 9999 | 2 | mean/drop | mixed |
| CU\* | 6 | 1=temp avg, 4=temp std | 0.1 | 9999 | 2, 5 | mean/drop | mixed |
| CV\* | 12 | 1=min temp, 4=min time, 7=max temp, 10=max time | 0.1 | 9999 | 2, 5, 8, 11 | mean/drop | mixed |
| CW\* | 6 | 1=wetness ch1, 4=wetness ch2 | 0.1 | 99999 | 2, 5 | mean/drop | mixed |
| CX\* | 12 | 1=precip total, 4=freq avg, 7=freq min, 10=freq max | 0.1 | 99999, 9999 | 2, 5, 8, 11 | mean/drop | mixed |
| GE1 | 4 | 1=convective cloud code, 3-4=base height range | 1 | 99999 | — | drop/mean | mixed |
| SA1 | 2 | 1=SST | 0.1 | 999 | 2 | mean | numeric |
| UA1 | 6 | 1=method, 2=period (sec), 3=wave ht, 5=sea state | 1, 0.1 | 99, 999 | 4, 6 | mean/drop | mixed |
| UG1 | 4 | 1=period (sec), 2=swell ht, 3=direction | 1, 0.1, 1 | 99, 999, 999 | 4 | mean/circular_mean | mixed |

Notes:
- UA1 method code and sea state are categorical and are excluded from aggregation; wave measurement quality (part4) gates parts 1-3; sea state quality is part6 and gates part5.
- UG1 swell direction uses a circular mean during aggregation when present; primary swell quality (part4) gates parts 1-3.
- UA1/UG1 quality codes are restricted to {0, 1, 2, 3, 9} per ISD marine specs.
- Additional cloud/solar groups parsed: GD*, GH1, GJ1, GK1, GL1, GM1, GN1, GO1, GP1, GQ1, GR1.
- Additional sections parsed: CRN/network metadata (CB*, CF*, CG*, CH*, CI1, CN*, CO*, CR1, CT*, CU*, CV*, CW1, CX*), marine (UA1, UG1/UG2, WA1, WD1, WG1, WJ1), runway visual range (ED1), soil/ground/pressure extensions (IA*, IB*, IC1, ST1, ME1/MF1/MG1/MH1/MK1).

---

## Specification Compliance & Validation

### Spec Coverage System

The pipeline now includes comprehensive specification-compliance tracking via an automated **spec coverage generator** (`tools/spec_coverage/generate_spec_coverage.py`) that:

- Parses the deterministic NOAA markdown source at `isd-format-document-parts/isd-format-document.deterministic.md`
- Derives compatibility `spec_part` groupings from ordered section anchors in that single source document
- Extracts roughly 3,500 specification rules covering sentinels, ranges, domains, quality codes, widths, and cardinality constraints
- Assigns deterministic content-based `rule_id` values while preserving global line provenance in the source markdown
- Matches extracted rules against implementation in `constants.py` and test coverage in `test_cleaning.py`
- Generates [SPEC_COVERAGE_REPORT.md](SPEC_COVERAGE_REPORT.md) showing:
  - implementation and strict-test coverage across the extracted rule inventory
  - Top gaps and actionable priorities for improving coverage

Run the coverage generator:

```bash
python tools/spec_coverage/generate_spec_coverage.py
```

This produces `spec_coverage.csv` and regenerates `SPEC_COVERAGE_REPORT.md`.

### Validation Infrastructure

Two new comprehensive validation documents guide pipeline correctness:

- [docs/PIPELINE_DESIGN_RATIONALE.md](docs/PIPELINE_DESIGN_RATIONALE.md) — Architecture decisions for spec-constrained cleaning, rule extraction, and enforcement layers
- [docs/PIPELINE_VALIDATION_PLAN.md](docs/PIPELINE_VALIDATION_PLAN.md) — Mandatory validation tracks (golden-file tests, real-station regression, completeness audits) with KPIs for production readiness

### Suspicious Coverage Monitoring

A GitHub Actions workflow (`.github/workflows/suspicious_coverage.yml`) automatically detects **suspicious coverage** — cases where tests claim to cover a spec rule but the rule is not marked as implemented in code. This prevents false-positive coverage metrics.

- Current suspicious entries: **407** (11.3% of rules)
- See [docs/validation_artifacts/suspicious_coverage/suspicious_summary.md](docs/validation_artifacts/suspicious_coverage/suspicious_summary.md) for the latest report

---

## Enhanced Test Suite

The test suite has been significantly expanded since February 19, 2026:

| File | Tests | What it covers |
|------|-------|----------------|
| `tests/test_cleaning.py` | 124 → **1,955+** | Comprehensive sentinel detection, scale factors, quality-flag filtering, domain enforcement across all field families |
| `tests/test_aggregation.py` | 19 | Column classification, per-field agg functions, categorical exclusion |
| `tests/test_integration.py` | 165 | End-to-end checks across 11 real station outputs |
| `tests/test_qc_comprehensive.py` | **803** (new) | QC signal handling for malformed tokens, sentinel edge cases, and boundary conditions |
| `tests/test_spec_coverage_generator.py` | **874** (new) | Spec rule extraction, identifier recognition, rule deduplication, coverage matching |
| `tests/test_suspicious_coverage_integrity.py` | **84** (new) | Validates suspicious coverage reports and ensures test/code alignment tracking |

Total test count: **3,800+** (up from ~308)

### QC Signal Enhancements

Quality control signal handling has been refined to handle:

- Malformed tokens (non-numeric values in expected-numeric fields)
- Sentinel values properly marked in QC status/reason columns
- Boundary conditions at min/max spec ranges
- Improved accuracy in `{FIELD}__qc_pass`, `__qc_status`, and `__qc_reason` columns

---

## Roadmap

See [CLEANING_RECOMMENDATIONS.md](CLEANING_RECOMMENDATIONS.md) for the full list of
completed and planned improvements, including:

- **P0 ✅** — Sentinel removal, scale factors, per-value quality-flag mapping
- **P1 ✅** — Categorical exclusion from aggregation, field-appropriate agg functions
- **P2 ✅** — Human-readable column names, unit-conversion options
- **P3 (in progress)** — Precipitation groups AA/AJ/AU and daily present weather AT implemented; derived quantities (RH, wind chill, heat index)
  and additional precipitation groups pending

### Current Focus: Specification Compliance

The pipeline is now focused on achieving **95%+ strict test coverage** of metric-eligible spec rules and eliminating sentinel leakage, scale-factor bugs, and quality-flag misapplication across all ~867 NOAA field identifiers.
