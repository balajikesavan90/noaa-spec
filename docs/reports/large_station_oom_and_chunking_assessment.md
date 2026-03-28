# INTERNAL DEVELOPMENT RECORD — NOT REVIEWER EVIDENCE

# Large-Station OOM Assessment And Chunked Processing Proposal

## Context

A batch cleaning run for build `20260318T061525Z` completed `95/100` stations and failed `5/100`.

Failed stations:

- `99999903047`
- `99999903048`
- `99999904126`
- `99999904130`
- `99999963829`

The user proposed a simple mitigation: split very large station inputs into smaller files, clean them one at a time, then collate the outputs.

This note records the observed evidence, the basis for the out-of-memory diagnosis, and an implementation design for that proposal that preserves the repository's scientific artifact contracts.

## What Was Observed

From the build monitor and run status artifacts for build `20260318T061525Z`:

- `completed: 95 / 100`
- `failed: 5`
- all failed stations had:
  - `status=failed`
  - `retry_count=2`
  - `last_exit_code=-9`
  - `failure_stage=child_process_crash`
  - `last_error_summary=station worker exited without error output`

Per-station status inspection showed:

- no worker result JSON written for any failed station
- no canonical output directory created for any failed station
- no structured Python traceback captured by the runner

The runner log pattern was:

1. first attempt starts
2. worker exits without error output
3. retry starts
4. worker exits without error output again
5. station marked failed

The five failed stations were also the five largest inputs in the batch.

Approximate input characteristics:

- failed set: `49.1 MB` to `49.7 MB`, roughly `2.04M` to `2.08M` rows each
- largest completed station: `30.7 MB`, `616,633` rows

This is a large step increase in row count, not just a small increase in file size.

## Why This Looks Like OOM

The strongest evidence came from kernel logs:

- `Out of memory: Killed process ... (python)`
- observed anonymous resident memory near `29-30 GB`

This confirms the failing worker processes were killed by the kernel OOM path rather than by:

- a handled Python exception
- the runner's timeout logic
- a deterministic output-validation failure

Additional evidence supporting OOM:

- failed workers exited with code `-9`, consistent with `SIGKILL`
- `station_timeout_seconds` was `null`, so the runner did not kill them for timeout
- no stdout/stderr traceback was emitted before death
- the process died before writing the worker result sidecar or success marker
- the failures cluster exactly on the largest station inputs

## Why The Current Worker Path Is Memory-Heavy

The current station worker path in `src/noaa_spec/cleaning_runner.py` is structurally expensive for very large station files:

1. read the entire raw parquet into a full pandas DataFrame
2. copy the raw DataFrame before cleaning
3. clean with `keep_raw=True`
4. hold both raw and cleaned frames in memory
5. optionally build station quality profile from the cleaned frame
6. optionally build domain split outputs from the cleaned frame
7. write final outputs

For normal stations this is acceptable. For `~2M` row stations it pushes memory into a non-linear failure zone.

The issue therefore appears to be a scaling problem in execution strategy, not a NOAA rule regression.

## Second Opinion On The "Dumb" Idea

The idea is not dumb. It is the right class of fix.

The important constraint is:

- split execution internally
- do not split the published artifact contract externally

The repository's contract is station-level canonical outputs, domain outputs, quality evidence artifacts, and manifests. That contract should remain unchanged.

So the recommended implementation is:

1. partition a very large station input into deterministic chunks
2. clean one chunk at a time
3. write temporary cleaned chunk outputs
4. collate the cleaned chunks into the final station-level canonical artifact
5. derive station-level domain and quality artifacts from the collated result or from merge-safe chunk summaries

That preserves reproducibility and lineage while reducing peak memory.

## Why Chunked Processing Fits This Repository

This repository is a specification-constrained publication system with deterministic artifacts.

Chunked processing is compatible with that model if the following remain true:

- chunk boundaries are deterministic
- chunk processing order is deterministic
- collation order is deterministic
- final station-level artifact schema is unchanged
- release manifests still describe station-level artifacts
- original station raw input remains the lineage root

Most cleaning operations in the current system are row-local or row-independent field expansions. That makes chunked execution a good fit.

## Design Constraints

Any chunked implementation must preserve:

- deterministic serialization
- deterministic row ordering
- stable schema and column naming
- station-level lineage
- station-level quality evidence semantics
- release layout and manifest contracts

It must not silently change:

- row inclusion/exclusion semantics
- null semantics
- QC flag behavior
- final domain dataset joinability

## Recommended Chunking Strategy

### Preferred Internal Strategy

Use deterministic station-internal chunking only for large inputs.

Good chunk boundary choices, in order:

1. parquet row groups, if they are stable and large enough to reduce memory
2. fixed row-count chunks, for example `100k` or `250k` rows
3. deterministic date-window chunks, only if row-order and edge handling remain simple

The simplest first implementation is fixed row-count chunks driven by stable input row order.

### Why Fixed Row-Count Is The Best First Step

- easy to reason about
- easy to test for equivalence against whole-file cleaning
- independent of assumptions about time continuity
- deterministic if row order is preserved

## Proposed Execution Model

### Phase 1: Chunk Planning

For each station input:

- inspect row count
- if below threshold, use the current whole-file path
- if above threshold, plan chunks deterministically

Example metadata:

- `chunk_index`
- `row_start`
- `row_end`
- `row_count`

### Phase 2: Per-Chunk Cleaning

For each chunk, in chunk order:

1. load chunk into memory
2. clean chunk using the existing cleaning semantics
3. normalize canonical contract columns
4. write cleaned chunk artifact to a temp directory
5. emit optional per-chunk summary metrics needed for later reduction

Temporary chunk outputs should be runtime artifacts, not publication artifacts.

### Phase 3: Canonical Collation

After all chunks succeed:

1. read cleaned chunk artifacts in chunk order
2. concatenate deterministically
3. write the final station-level `LocationData_Cleaned.parquet`

Collation must preserve the same row ordering policy as whole-file processing.

### Phase 4: Downstream Artifact Generation

After station-level canonical collation:

- generate domain splits from the collated cleaned dataset
- generate station quality profile from the collated cleaned dataset or from merge-safe summaries
- write success marker only after all expected outputs are present and valid

## What Can Be Aggregated Safely Per Chunk

Some metrics are naturally reducible and can be merged without rereading all chunks:

- row counts
- null counts by identifier
- QC flag counts by identifier
- rule-family impact counts
- per-domain usable row counts

These are additive reductions if defined carefully.

However, the first implementation should prefer correctness over maximal optimization. It is acceptable to collate the canonical dataset first and then compute downstream station artifacts from the collated cleaned output if memory permits.

## Implementation Details

### New Internal Threshold

Add a chunking threshold for batch mode only.

Candidate triggers:

- row count threshold
- input size threshold
- explicit CLI opt-in for initial rollout

Row count is the better trigger because the observed failures correlate much more strongly with row cardinality than raw file size alone.

### Suggested New Internal Helpers

Potential additions in `src/noaa_spec/cleaning_runner.py`:

- `_should_use_chunked_station_processing(...)`
- `_plan_station_chunks(...)`
- `_read_raw_chunk(...)`
- `_clean_station_chunk(...)`
- `_write_cleaned_chunk(...)`
- `_collate_cleaned_chunks(...)`
- `_reduce_chunk_quality_summaries(...)`

### Temporary Runtime Layout

Use a runtime-only temp directory under the build tree, for example:

```text
build_<run_id>/
  manifests/
  canonical_cleaned/
  quality_reports/
  domains/
  .runtime/
    station_chunks/
      <station_id>/
        chunk_00000_cleaned.parquet
        chunk_00001_cleaned.parquet
        ...
```

These files should not be included in publication manifests.

### Success Criteria

The station is complete only if:

- all chunks succeed
- collation succeeds
- final canonical artifact exists
- downstream station artifacts succeed
- success marker validates

### Failure Handling

If any chunk fails:

- mark station failed or retryable
- keep diagnostics
- do not write success marker
- do not publish partial collated outputs

### Logging Improvements

Whether or not chunking is implemented, the runner should persist per-attempt logs for:

- worker stdout
- worker stderr
- chunk index if chunking is active

This would materially improve postmortem diagnostics.

## Determinism Considerations

Chunking changes execution, so determinism must be tested explicitly.

Required invariants:

- whole-file cleaning and chunked cleaning produce byte-equivalent or contract-equivalent outputs for the same station input
- row ordering is stable
- schema is identical
- quality profiles and domain outputs are identical or intentionally equivalent under deterministic reduction

Recommended tests:

1. small fixture station cleaned whole vs chunked yields identical canonical output
2. domain split outputs match whole-file baseline
3. station quality profile matches whole-file baseline
4. repeated chunked runs produce identical checksums
5. final manifests exclude temporary chunk artifacts

## Lowest-Risk Rollout Plan

### Step 1

Add better crash diagnostics:

- persist worker stdout/stderr per attempt
- persist memory-related phase breadcrumbs if practical

### Step 2

Add chunked canonical cleaning only for oversized stations:

- chunk input
- clean chunk
- collate canonical dataset

Keep downstream artifact generation unchanged initially.

### Step 3

If needed, optimize downstream station quality and domain generation to reduce post-collation memory.

### Step 4

Add deterministic equivalence tests and a large-station smoke test.

## Recommendation

The proposed "split large stations into smaller files, clean one at a time, then collate" approach should be treated as a serious implementation path, not a fallback hack.

It directly addresses the confirmed OOM failure mode while remaining compatible with the repository's publication model, provided that:

- chunking remains an internal execution detail
- station-level artifacts remain the public contract
- deterministic collation and lineage are preserved

This is the most pragmatic next step for making the batch cleaner scale to the largest pulled stations without weakening artifact integrity.
