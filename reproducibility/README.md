# Reproducibility

This folder contains a minimal, deterministic cleaning example plus a pipeline snapshot artifact.

## Run cleaning pipeline (example)

```bash
python reproducibility/run_pipeline_example.py
```

This reads reproducibility/sample_station_raw.txt and overwrites reproducibility/sample_station_cleaned.csv.

Optional: write the cleaned CSV to a custom path instead of overwriting the repo file:

```bash
python reproducibility/run_pipeline_example.py --out /tmp/sample_station_cleaned.csv
```

## Run coverage generator

```bash
python tools/spec_coverage/generate_spec_coverage.py
```

## Run tests

```bash
pytest -q
```

## Data provenance

The sample station data is a synthetic, minimal extract based on the NOAA ISD
Global Hourly CSV schema. It uses a placeholder station ID and two rows of
well-formed TMP, DEW, and SLP fields to exercise scaling, quality parsing, and
QC signal generation without relying on external data downloads.

Pipeline transformations applied by the example script:

- Read the raw CSV into a DataFrame.
- Parse comma-encoded fields (TMP, DEW, SLP) in strict mode.
- Apply missing-value checks, quality filtering, and min/max range enforcement.
- Scale numeric values per field rules and emit QC columns.
- Produce row-level usability summaries.

## Archived full station reports

The full historical station-report example tree is stored locally at:

`data/archive/station_reports_full/docs/examples/station_reports/`

Only a curated subset remains tracked under `docs/examples/stations/`.
