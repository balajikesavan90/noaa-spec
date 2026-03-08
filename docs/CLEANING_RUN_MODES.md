# Cleaning Run Modes

This document defines the production-safe cleaning runner:

```bash
poetry run python -m noaa_climate_data.cli cleaning-run ...
```

## Why This Exists

- Raw parquet input trees (for example on an external drive) are treated as **read-only** sources.
- Cleaned outputs, manifests, reports, and quality profiles are written to separate artifact roots.
- Batch runs are resumable and deterministic via `run_manifest.csv`, `run_status.csv`, and per-station `_SUCCESS.json` markers.

## Supported Modes

### `test_csv_dir`

Use for local CSV iteration/debugging.

Input expectation:

- `<input-root>/<station_id>/LocationData_Raw.csv`
- station folder name must be exactly 11 digits (`^\d{11}$`)

Default write behavior:

- cleaned station outputs: on
- domain splits: on
- station quality profiles: on
- station reports: off
- global summary: off

### `batch_parquet_dir`

Use for long-running parquet batch cleaning.

Input expectation:

- `<input-root>/<station_id>/LocationData_Raw.parquet`
- station folder name must be exactly 11 digits (`^\d{11}$`)

Default write behavior:

- cleaned station outputs: on
- domain splits: off
- station quality profiles: on
- station reports: off
- global summary: on

## Path Separation and Safety

The runner only reads from `--input-root` and never writes into it.

Do not point any write root inside the input root. The runner rejects this configuration.

Write roots:

- `--output-root`
- `--reports-root`
- `--quality-profile-root`
- `--manifest-root`

Recommended layout (auto-derived if not provided):

- test runs: `artifacts/test_runs/<run_id>/...`
- parquet runs: `artifacts/parquet_runs/<run_id>/...`

## Manifest-First and Cron-Job Coexistence

For `batch_parquet_dir`, `--manifest-first` defaults to enabled.

Behavior:

1. Discover eligible stations.
2. Snapshot deterministic `run_manifest.csv`.
3. Process only stations from that manifest.

This isolates the run from concurrent cron-job updates in the raw input tree.

## Run Configuration Fingerprint Guardrail

Each run writes `run_config.json` in `--manifest-root` with a canonical fingerprint.

If `--run-id` already exists:

- exact same config: allowed
- different config: fails loudly
- to reuse the same `run_id` with new config, pass `--manifest-refresh`

`run_config.json` covers mode, input root/format, filters, limits, write flags, and write roots.

## Resumability and Completion Rules

A station is considered complete only when all are true:

1. `run_status.csv` marks station `completed`
2. all expected enabled outputs exist
3. station `_SUCCESS.json` exists and matches run/station/expected outputs

If status says completed but marker or outputs are missing, the station is recomputed.

## Low-I/O Quality Profiles

Station quality profiles are computed in-memory from the cleaned DataFrame during processing.

- no reread of cleaned outputs for profile generation
- profile sidecars written as: `quality_profiles/station_<station_id>.json`

Optional global summary (`reports/global_quality_summary.json`) is built from sidecars, not cleaned station datasets.

## Common Commands

### Local CSV test mode

```bash
poetry run python -m noaa_climate_data.cli cleaning-run \
  --mode test_csv_dir \
  --input-root outputs \
  --input-format csv
```

### Production parquet batch mode

```bash
poetry run python -m noaa_climate_data.cli cleaning-run \
  --mode batch_parquet_dir \
  --input-root /media/<user>/LaCie/NOAA_Data \
  --input-format parquet
```

### Resume a prior run id

```bash
poetry run python -m noaa_climate_data.cli cleaning-run \
  --mode batch_parquet_dir \
  --input-root /media/<user>/LaCie/NOAA_Data \
  --input-format parquet \
  --run-id 20260307T091500Z
```

### Refresh manifest/config for same run id (explicit)

```bash
poetry run python -m noaa_climate_data.cli cleaning-run \
  --mode batch_parquet_dir \
  --input-root /media/<user>/LaCie/NOAA_Data \
  --input-format parquet \
  --run-id 20260307T091500Z \
  --manifest-refresh
```

### Toggle heavy outputs

```bash
# Turn on station reports explicitly
poetry run python -m noaa_climate_data.cli cleaning-run \
  --mode test_csv_dir \
  --input-root outputs \
  --input-format csv \
  --write-station-reports

# Turn off domain splits
poetry run python -m noaa_climate_data.cli cleaning-run \
  --mode test_csv_dir \
  --input-root outputs \
  --input-format csv \
  --no-write-domain-splits
```

When `--write-station-reports` is enabled, cleaning-run writes:

- `LocationData_QualityReport.json`
- `LocationData_QualityReport.md`
- `LocationData_QualitySummary.csv`
- domain quality sidecars under `reports/<station_id>/domain_quality/`

Cleaning-run station reports no longer write aggregation report artifacts.
