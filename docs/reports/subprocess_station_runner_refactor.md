# Subprocess Station Runner Refactor

## Architecture Change

The cleaning runner now isolates each station in a fresh subprocess.

- The parent process remains the orchestration source of truth.
- The child process handles exactly one station and reuses the existing station cleaning/write path.
- Per-station artifact names and output paths remain unchanged.
- Parent-owned run artifacts remain under:
  - `manifests/run_config.json`
  - `manifests/run_manifest.csv`
  - `manifests/run_status.csv`
  - `manifests/run_state.json`

The parent now:

- loads or creates the run manifest/config
- selects pending stations
- launches one worker subprocess per station
- captures exit code, timeout, and stderr summary
- validates expected outputs plus `_SUCCESS.json`
- updates `run_status.csv`
- decides whether run-level publication artifacts may be written

The worker now:

- reads one station raw input
- runs the existing cleaning logic unchanged
- writes canonical output
- writes domain outputs
- writes station quality/report artifacts
- writes `_SUCCESS.json` only after expected per-station outputs exist

## Failure Semantics

Station worker failures no longer kill the parent batch coordinator.

- nonzero exit, crash, or timeout: parent survives and records failure metadata
- `run_status.csv` now includes:
  - `retry_count`
  - `last_exit_code`
  - `failure_stage`
  - `last_error_summary`
- a station is never marked `completed` unless:
  - all expected enabled outputs exist
  - `_SUCCESS.json` exists
  - `_SUCCESS.json` matches run/station/expected outputs

If a worker exits successfully but output validation fails, the parent marks the station failed instead of accepting a false completion.

## Retry Semantics

Retries are parent-controlled and configurable with `--max-station-retries`.

- default behavior: one retry after the initial failed attempt
- retry budget is enforced per invocation
- `retry_count` in `run_status.csv` is cumulative across invocations
- retrying stations are recorded as `retrying` between failed and subsequent attempts

Optional per-station timeout is available through `--station-timeout-seconds`.

## Publication and Finalization Semantics

Run-level publication artifacts are now gated on truthful run completion.

- completed run:
  - writes mandatory run-level quality artifacts
  - writes `quality_assessment.json`
  - writes `release_manifest.csv`
  - writes `file_manifest.csv`
  - writes `publication_readiness_gate.json`
- failed or interrupted run:
  - does not emit those finalization artifacts as if the build were complete
  - removes stale copies of those artifacts if they exist from an earlier incomplete invocation
  - writes `run_state.json` with the terminal state

This preserves the artifact split:

- `publication_readiness_gate.json`: integrity/build artifact
- `quality_assessment.json`: advisory quality artifact

Both are now produced only when the batch has genuinely completed.
