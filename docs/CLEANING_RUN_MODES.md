# Cleaning Run Modes

This document defines the production-safe cleaning runner:

```bash
poetry run python -m noaa_climate_data.cli cleaning-run ...
```

## Why This Exists

- Raw parquet input trees (for example on an external drive) are treated as **read-only** sources.
- Cleaned outputs, manifests, reports, and quality profiles are written to separate artifact roots.
- Batch runs are resumable and deterministic via `run_manifest.csv`, `run_status.csv`, and per-station `_SUCCESS.json` markers.
- Each station is executed in a fresh subprocess so a station-level crash does not kill the parent coordinator.

## Supported Modes

### `test_csv_dir`

Use for local CSV iteration/debugging.

Input expectation:

- `<input-root>/<station_id>/LocationData_Raw.csv`
- station folder name must be exactly 11 alphanumeric characters (`^[A-Za-z0-9]{11}$`)

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
- station folder name must be exactly 11 alphanumeric characters (`^[A-Za-z0-9]{11}$`)

Default write behavior:

- cleaned station outputs: on
- domain splits: on
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

- all modes: `release/build_<run_id>/{canonical_cleaned,domains,quality_reports,manifests}`

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

## `run_manifest` vs `run_status` Semantics

- `run_manifest.csv` is a discovery snapshot for the run scope.
- It is refreshed only when `--manifest-refresh` is used.
- It is not the execution truth table; it is a deterministic station/input snapshot.

- `run_status.csv` is the execution truth table.
- It mutates as stations transition across runtime states (`pending`, `running`, `retrying`, `completed`, `failed`, `skipped_*`).
- Resume/recovery behavior must consult `run_status.csv` plus `_SUCCESS.json` and expected output existence checks.
- It also records parent-owned retry/failure metadata:
  - `retry_count`
  - `last_exit_code`
  - `failure_stage`
  - `last_error_summary`

## Subprocess-Per-Station Orchestration

The parent process owns:

- `run_config.json`, `run_manifest.csv`, and `run_status.csv`
- station selection and resume logic
- subprocess launch, timeout handling, stderr capture, and bounded retries
- terminal run-state determination and finalization gating

The child worker process owns exactly one station:

- read raw input
- run the existing cleaning logic unchanged
- write canonical, domain, and station-quality/report artifacts
- write `_SUCCESS.json` only after all expected per-station outputs exist

For oversized stations, the worker may switch to internal fixed-row chunking.

- chunking is a runtime-only execution strategy, not a publication contract change
- station-level canonical/domain/quality outputs remain the only public artifacts
- cleaned chunks are written under `release/build_<run_id>/.runtime/station_chunks/<station_id>/`
- runtime chunk artifacts are excluded from release manifests and file manifests
- default chunking policy uses a `250,000`-row threshold and `250,000`-row fixed chunks
- chunk order and collation order are deterministic so station row ordering and cleaning semantics remain stable

Relevant CLI controls:

- `--max-station-retries`
- `--station-timeout-seconds`

## Publication Readiness vs Advisory Quality

`manifests/publication_readiness_gate.json` is integrity-only. It covers build/package checks such as:

- artifact existence and manifest coverage
- checksum and timestamp integrity
- structural sanity of required quality artifacts
- build metadata completeness

Threshold-based quality findings now live in `quality_reports/quality_assessment.json`.

Reference values are still emitted for advisory interpretation in that artifact:

- quality-code exclusion reference rate: `0.25`
- domain usability reference minima by domain:
  - `core_meteorology`: `0.50`
  - `wind`: `0.00`
  - `precipitation`: `0.00`
  - `clouds_visibility`: `0.00`
  - `pressure_temperature`: `0.00`
  - `remarks`: `0.00`

These reference checks are emitted in `quality_reports/quality_assessment.json` for
advisory interpretation. Threshold failures are reported there, but they do not
control the top-level `passed` result in `manifests/publication_readiness_gate.json`.

Run-level publication artifacts are emitted only for a truthful completed run.

- completed run: writes release/file manifests, advisory quality assessment, and publication readiness gate
- failed/interrupted/partial run: does not leave those finalization artifacts behind
- `manifests/run_state.json` always records whether the run is `completed`, `failed`, or `interrupted`

## Resumability and Completion Rules

A station is considered complete only when all are true:

1. `run_status.csv` marks station `completed`
2. all expected enabled outputs exist
3. station `_SUCCESS.json` exists and matches run/station/expected outputs

If status says completed but marker or outputs are missing, the station is recomputed.

If a worker exits `0` but expected outputs or `_SUCCESS.json` validation fail, the parent marks the station failed rather than accepting a false completion.

## Low-I/O Quality Profiles

Station quality profiles are computed during processing from cleaned station rows.

- whole-file stations compute profiles directly from the in-memory cleaned DataFrame
- chunked stations merge deterministic per-chunk profiles before writing the final sidecar
- profile sidecars written under: `quality_reports/station_quality/station_<station_id>.json`

Optional global summary (`quality_reports/global_quality_summary.json`) is built from sidecars, not cleaned station datasets.

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
  --input-format parquet \
  --max-station-retries 1
```

### Frozen pulled-station batch helper

```bash
poetry run python -m noaa_climate_data.cli run-cleaning-batch \
  --raw-root /media/<user>/LaCie/NOAA_Data \
  --count 100
```

Behavior:

- selects a deterministic subset of stations already marked pulled in `raw_pull_state.csv`
- excludes station IDs already recorded in prior batch `manifests/run_manifest.csv` files under the release base root
- stages those raw parquets into a frozen input tree
- invokes `cleaning-run --mode batch_parquet_dir` against the staged input root
- keeps the raw ingest cron and the cleaning batch separated at the filesystem boundary
- writes release outputs to `<raw-root-parent>/NOAA_CLEANED_DATA/build_<run_id>/...` by default

Selection strategies:

- `size_quartiles` (default): balanced rehearsal sample across small/medium/large raw parquet sizes, spread across each quartile range, with explicit top-tail picks from the largest available files
- `station_id`: deterministic first-N by canonical station ordering for declared publication scope

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
  --no-domain-splits
```

`run_status.csv` now records per-station phase timings and descriptive workload metrics, including:

- `elapsed_read_seconds`
- `elapsed_clean_seconds`
- `elapsed_domain_split_seconds`
- `elapsed_quality_profile_seconds`
- `elapsed_write_seconds`
- `elapsed_total_seconds`
- `row_count_raw`
- `row_count_cleaned`
- `raw_columns`
- `cleaned_columns`
- `input_size_bytes`
- `cleaned_size_bytes`

When domain splits are disabled, `domain_usability_summary.csv` stays present but marks rows as
fallback/advisory output using `artifact_mode=fallback_no_domain_splits` and `advisory_only=true`.

When `--write-station-reports` is enabled, cleaning-run writes:

- `LocationData_QualityReport.json`
- `LocationData_QualityReport.md`
- `LocationData_QualitySummary.csv`
- domain quality sidecars under `reports/<station_id>/domain_quality/`

Cleaning-run station reports no longer write aggregation report artifacts.
