# NOAA file index (2026-02-07)

This folder contains the NOAA Global Hourly file index and year-counts used by the pipeline.

## How it was generated

### Pre Metadata

- `DataFileList.csv`: all available file names by year in the 1975–2025 range.
- `DataFileList_YEARCOUNT.csv`: number of years each file appears in within 1975–2025.

#### Command:

- `poetry run python -m noaa_spec.cli file-list --start-year 1975 --end-year 2025 --sleep-seconds 0.5 --retries 3 --backoff-base 0.5 --backoff-max 8`

#### Behavior:
- Scrapes the NOAA Global Hourly directory listing for available year folders.
- For each year, scrapes the list of `.csv` files.
- Builds a file list (`DataFileList.csv`) with `YEAR` + `FileName`.
- Aggregates year counts per file into `DataFileList_YEARCOUNT.csv`.
- Uses retries with exponential backoff and a 0.5s delay between year requests.

#### Notes
- Output folder naming uses UTC date (`YYYYMMDD`).
- This index does not download station data; it only lists available files.

### Station metadata (Stations.csv)

- `Stations.csv`: immutable station metadata with year coverage fields.

#### Command:

- `poetry run python -m noaa_spec.cli location-ids --start-year 1975 --end-year 2025 --sleep-seconds 0.5 --retries 3 --backoff-base 0.5 --backoff-max 8`

#### Behavior:
- Reads `DataFileList_YEARCOUNT.csv` to identify stations with coverage in the selected year range.
- Fetches NOAA station metadata and joins it to the file list.
- Computes coverage fields (`No_Of_Years`, `FIRST_YEAR`, `LAST_YEAR`, `YEAR_COUNT`).
- Marks completeness via `METADATA_COMPLETE` and writes `Stations.csv`.

#### Notes
- Creation started on 2026-02-07.
- Metadata collection for all 27k stations completed on 2026-02-12.
- **2026-02-21 Recovery**: Internet outage on 2026-02-20 interrupted the `location-ids` metadata fetch process mid-recovery, causing loss of 3,748 station records from Stations.csv. All 27,486 stations have been recovered and restored. Full recovery log preserved in `recovery_log_20260221_194705.csv`.

### Raw data pulls (cron)

#### Outputs:

- `output/<station_id>/LocationData_Raw.parquet`: raw NOAA data per station.
- `noaa_file_index/state/raw_pull_state.csv`: operational raw pull state keyed by station/file.
- `noaa_file_index/state/raw_pull_state.csv.lock`: non-blocking overlap lock for cron execution.

#### Command:

- `scripts/run_pick_location_cron.sh`
- `poetry run python -m noaa_spec.cli materialize-raw-pull-state`

The cron wrapper exports `PYTHONPATH=<repo>/src` before invoking `poetry run`
so the scheduled job still resolves `noaa_spec.cli` even if the Poetry
environment no longer has the package installed in editable mode.

#### Behavior:
- Reads the immutable `Stations.csv` registry snapshot.
- Reads operational state from `noaa_file_index/state/raw_pull_state.csv`.
- Picks a random station not yet marked as pulled in the raw pull state file.
- Downloads yearly NOAA CSVs with 0.5s delay between requests.
- Writes `LocationData_Raw.parquet` to the external output directory.
- Records the successful pull in `noaa_file_index/state/raw_pull_state.csv`.
- Exits without doing work if another `pick-location` process already holds the raw pull lock.
- `materialize-raw-pull-state` backfills `raw_pull_state.csv` from legacy `raw_data_pulled` flags and rewrites `Stations.csv` without operational status columns.

#### Notes
- Cron schedule runs every 5 minutes.
- Schedule started on 2026-02-13.

### Data cleaning

#### Outputs:

- `output/<station_id>/LocationData_Cleaned.parquet`: cleaned station data.
- `release/build_<build_id>/...`: canonical/domain/quality/manifest publication artifacts for `cleaning-run`.

#### Commands:

- Single-file cleaning:
  `poetry run python -m noaa_spec.cli clean-parquet output/<station_id>/LocationData_Raw.parquet`
- Batch cleaning orchestration:
  `poetry run python -m noaa_spec.cli cleaning-run --mode <mode> --input-root <root> --input-format parquet`

#### Notes

- This dated index folder stores index and station metadata snapshots.
- It is not the execution state surface for cleaning jobs.
- Runtime cleaned/domain/quality/manifests publication outputs are produced under runtime output roots (for example `release/build_<build_id>/...`), not inside this index snapshot folder.

### Data aggregation

This index snapshot does not store aggregation outputs. Aggregated artifacts are produced by the runtime processing workflows and should be tracked in their designated release/output roots.
