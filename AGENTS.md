# instructions for noaa-climate-data

## Big picture
- Python rewrite of legacy R scripts; the pipeline is split across `noaa_client` (remote listing/download), `cleaning` (comma-encoded field expansion), and `pipeline` (end-to-end transforms). See [src/noaa_climate_data/noaa_client.py](src/noaa_climate_data/noaa_client.py), [src/noaa_climate_data/cleaning.py](src/noaa_climate_data/cleaning.py), and [src/noaa_climate_data/pipeline.py](src/noaa_climate_data/pipeline.py).
- Target outputs for researchers: `raw_parquet` (immutable ingest), `cleaned_parquet` (standardized columns + quality flags), domain splits (temperature, dew, rainfall, wind, etc), and domain aggregates (monthly/yearly) built from the split datasets.
- Current top focus: make the cleaned dataset contract accurate and stable; downstream domain splits and aggregates come after cleaning quality is locked in.
- Data flow (current): list years/files → count year coverage → select full-coverage stations → download station CSVs → clean → add time columns → filter complete months/years → aggregate to monthly/yearly outputs.

## Source map (src/noaa_climate_data)
- [src/noaa_climate_data/__init__.py](src/noaa_climate_data/__init__.py): Package entry point; exposes public package metadata and keeps imports minimal to avoid side effects.
- [src/noaa_climate_data/constants.py](src/noaa_climate_data/constants.py): Shared constants (URLs, field scales, quality flags) used by the client, cleaning, and pipeline modules.
- [src/noaa_climate_data/noaa_client.py](src/noaa_climate_data/noaa_client.py): Remote listing/download helpers for NOAA Global Hourly CSVs; provides inputs to the pipeline and CLI.
- [src/noaa_climate_data/cleaning.py](src/noaa_climate_data/cleaning.py): Parsing and expansion of NOAA comma-encoded fields, scale/quality handling, and data normalization prior to aggregation.
- [src/noaa_climate_data/pipeline.py](src/noaa_climate_data/pipeline.py): Orchestrates end-to-end transforms, including time columns, completeness filters, best-hour selection, and aggregation.
- [src/noaa_climate_data/cli.py](src/noaa_climate_data/cli.py): CLI entry points that wire together the client, cleaning, and pipeline flows for file-listing and station processing.

## Key workflows (Poetry)
- Install: `poetry install` (from [README.md](README.md)).
- Run tests: `poetry run pytest tests/ -v`.
- Build file list + year counts: `poetry run python -m noaa_climate_data.cli file-list ...`.
- Build station metadata: `poetry run python -m noaa_climate_data.cli location-ids ...`.
- Process a station: `poetry run python -m noaa_climate_data.cli process-location <file>.csv ...`.

## Project-specific conventions
- Cleaning expands NOAA comma-encoded fields into `<column>__value`, `<column>__quality`, or `<column>__partN` columns; quality filtering uses `QUALITY_FLAGS` from [src/noaa_climate_data/constants.py](src/noaa_climate_data/constants.py).
- Temperature-like fields apply scale factors defined in `FIELD_SCALES` ([src/noaa_climate_data/cleaning.py](src/noaa_climate_data/cleaning.py)).
- Aggregation uses numeric mean across grouped columns; non-numeric columns are converted if possible ([_aggregate_numeric](src/noaa_climate_data/pipeline.py#L86)).
- “Best hour” is chosen by most unique days per hour; only that hour is kept before aggregation ([_best_hour](src/noaa_climate_data/pipeline.py#L57)).
- Monthly data requires ≥20 days per month and full 12-month years before yearly aggregation ([_filter_full_months](src/noaa_climate_data/pipeline.py#L64), [_filter_full_years](src/noaa_climate_data/pipeline.py#L69)).
- Output files for each station are written as `LocationData_*.csv` into `output/<station>/` via the CLI ([src/noaa_climate_data/cli.py](src/noaa_climate_data/cli.py)).

## Integration points
- External data source: NOAA Global Hourly CSVs at `BASE_URL` in [src/noaa_climate_data/constants.py](src/noaa_climate_data/constants.py).
- HTTP is only used for metadata existence checks (`requests.head`) and the remaining CSVs are read via `pandas.read_csv(url)`.

## When editing/adding code
- Keep functions pure where possible; `pipeline.py` orchestrates IO while `cleaning.py` focuses on parsing/transformations.
- Prefer pandas DataFrame transforms to match existing pipeline style; keep column naming consistent with `__value`, `__quality`, `__partN` patterns.