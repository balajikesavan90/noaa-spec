# Cleaning Run Modes

This section documents larger-run maintainer workflows. For a portable first run, use the core CLI and reproducibility fixture documented in the root README and REPRODUCIBILITY guide.

This document defines the production-safe cleaning runner:

```bash
poetry run noaa-spec cleaning-run ...
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

## Domain Artifact Presence Semantics

Domain datasets are written only when at least one cleaned row survives the domain projection for that station.

This means a completed station run may legitimately include:

- a canonical cleaned dataset,
- station and run-level quality artifacts,
- manifests and `_SUCCESS.json`,
- only a subset of possible domain datasets.

If a station has no valid data for a domain, or if no rows survive that domain-specific projection after cleaning and QC handling, the domain artifact is intentionally omitted. This is expected behavior, not a release-layout error.

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

## Publication Readiness vs Descriptive Quality Diagnostics

`manifests/publication_readiness_gate.json` is integrity-only. It covers build/package checks such as:

- artifact existence and manifest coverage
- checksum and timestamp integrity
- structural sanity of required quality artifacts
- build metadata completeness

Descriptive quality diagnostics live in `quality_reports/quality_assessment.json`.

That artifact reports observed exclusion, completeness, sparsity, and usability
metrics produced by NOAA-derived parsing, normalization, and QC semantics.
It does not compare those observations to repository-defined quality thresholds
and it does not prescribe acceptability.

Run-level publication artifacts are emitted only for a truthful completed run.

- completed run: writes release/file manifests, descriptive quality diagnostics, and publication readiness gate
- failed/interrupted/partial run: does not leave those finalization artifacts behind
- `manifests/run_state.json` always records whether the run is `completed`, `failed`, or `interrupted`
- completed run also writes `manifests/post_run_audit.md` after finalization as a companion audit snapshot of the finished build

`quality_reports/quality_assessment.json` is required to exist for a completed build and is included in the publication gate's manifest-coverage check. Its contents remain descriptive and do not drive the top-level integrity result.

## Finalization Order and Artifact Immutability

For a completed run, finalization now follows a strict order:

1. station-level and aggregate artifacts are fully written to their final paths
2. finalized artifact paths are checksum-registered from on-disk bytes
3. `release_manifest.csv` is built from that checksum registry
4. `quality_assessment.json` is written and checksum-registered
5. `file_manifest.csv` is built from the same checksum registry, with the planned gate checksum injected before the gate file is written
6. `publication_readiness_gate.json` is built from the final manifest snapshot and written last
7. `post_run_audit.md` is generated after finalization from the finished manifests, gate, and run state

After an artifact path is checksum-registered, any later write to that same finalized path is treated as a runtime error.

This prevents:

- manifest rows for the same path from disagreeing on checksum
- gate snapshots from being generated from stale intermediate manifests
- silent post-checksum rewrites of finalized artifacts

`post_run_audit.md` is intentionally a post-finalization companion artifact. It is not included in the integrity surfaces that `publication_readiness_gate.json` validates, so the audit can describe the final build without creating checksum recursion.

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
poetry run noaa-spec cleaning-run \
  --mode test_csv_dir \
  --input-root outputs \
  --input-format csv
```

### Production parquet batch mode

```bash
poetry run noaa-spec cleaning-run \
  --mode batch_parquet_dir \
  --input-root <EXTERNAL_STORAGE>/NOAA_Data \
  --input-format parquet \
  --max-station-retries 1
```

`<EXTERNAL_STORAGE>` is a placeholder from a local run environment and is not required for reproduction.

### Frozen pulled-station batch helper

```bash
poetry run noaa-spec run-cleaning-batch \
  --raw-root <EXTERNAL_STORAGE>/NOAA_Data \
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
poetry run noaa-spec cleaning-run \
  --mode batch_parquet_dir \
  --input-root <EXTERNAL_STORAGE>/NOAA_Data \
  --input-format parquet \
  --run-id 20260307T091500Z
```

### Refresh manifest/config for same run id (explicit)

```bash
poetry run noaa-spec cleaning-run \
  --mode batch_parquet_dir \
  --input-root <EXTERNAL_STORAGE>/NOAA_Data \
  --input-format parquet \
  --run-id 20260307T091500Z \
  --manifest-refresh
```

### Toggle heavy outputs

```bash
# Turn on station reports explicitly
poetry run noaa-spec cleaning-run \
  --mode test_csv_dir \
  --input-root outputs \
  --input-format csv \
  --write-station-reports

# Turn off domain splits
poetry run noaa-spec cleaning-run \
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

When domain splits are disabled, `domain_usability_summary.csv` stays present and marks rows with
`artifact_mode=fallback_no_domain_splits` so `__all__` summarizes canonical usability only.

When `--write-station-reports` is enabled, cleaning-run writes:

- `LocationData_QualityReport.json`
- `LocationData_QualityReport.md`
- `LocationData_QualitySummary.csv`
- domain quality sidecars under `reports/<station_id>/domain_quality/`

Cleaning-run station reports no longer write aggregation report artifacts.
