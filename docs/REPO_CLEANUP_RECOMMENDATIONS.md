# Repository Cleanup Recommendations (Second Pass)

Date: 2026-03-06  
Scope: Identification only. No files moved or deleted.

## Executive Summary

Main cleanup opportunity is generated data volume:

- `output/` is ~3.5 GB (largest bucket)
- `output/NOAA Demo Data/` alone is ~1.5 GB
- `noaa_file_index/20260207/` is ~19 MB of snapshot CSV data

Secondary cleanup opportunity is root-level file organization:

- Several operational/one-off scripts live at repo root
- Roadmap/planning docs live at repo root instead of `docs/`
- One script location does not match docs references

## Current Signals Considered

- Tracked files (`git ls-files`)
- Ignored files (`git status --ignored`)
- Actual disk usage (`du`)
- In-repo references via `rg` to avoid breaking paths silently

## Deletion Candidates

## 1) High-confidence generated/cache artifacts

These are safe cleanup candidates and are already ignored by `.gitignore`:

- `.coverage`
- `.pytest_cache/`
- `**/__pycache__/` under `src/`, `tests/`, `scripts/`, `tools/`
- `reprocess_timing_after.log`
- `reprocess_timing_full_after.log`

Recommendation: delete locally whenever you want a clean working tree footprint.

## 2) High-confidence local generated outputs (very large)

Ignored, regenerable, and currently taking most disk:

- `output/*/LocationData_{Raw,Cleaned,Hourly,Monthly,Yearly,QualitySummary}.csv`
- `output/NOAA Demo Data/*.csv`
- `noaa_file_index/20260207/{DataFileList.csv,DataFileList_YEARCOUNT.csv,Stations.csv,recovery_log_*.csv}`

Recommendation: keep only the minimum sample set you actively need; archive or remove the rest.

## 3) Medium-confidence analysis artifacts (regenerable but referenced in docs/tests)

These are ignored and regenerable, but some tooling expects them to exist locally:

- `spec_coverage.csv` (used by tests/tools/docs)
- `unspecified_29.csv`
- `spec_coverage_unspecified_filtered.csv`
- `spec_coverage_matching_unspecified_29.csv`
- `docs/validation_artifacts/suspicious_coverage/suspicious_cases_full.csv`
- `docs/validation_artifacts/suspicious_coverage/suspicious_cases_final.csv`

Recommendation: delete only if you are fine regenerating before running relevant tests/tools.

## Move/Reorganization Candidates

## 1) Root scripts -> tools/scripts folders (high confidence)

Current root files:

- `check_station_sync.py`
- `rerun_stations.py`
- `generate_audit_queue.py`

Suggested locations:

- `tools/ops/check_station_sync.py`
- `tools/ops/rerun_stations.py`
- `tools/spec_coverage/generate_audit_queue.py`

Why:

- Reduces root clutter
- Better groups maintenance utilities
- Aligns with existing `tools/spec_coverage/*`

Important note:

- `docs/PIPELINE_VALIDATION_PLAN.md` already references `tools/spec_coverage/generate_audit_queue.py`, but file currently lives at repo root. Move would fix this drift.

## 2) Root planning docs -> docs/roadmap (high confidence)

Current root docs:

- `NEXT_STEPS.md`
- `ARCHITECTURE_NEXT_STEPS.md`
- `P3_EXPAND_RESEARCH_VALUE.md`

Suggested location:

- `docs/roadmap/`

Why:

- Keeps root focused on package metadata + primary README
- Makes roadmap artifacts easier to discover as documentation

Caveat:

- `NEXT_STEPS.md` and `ARCHITECTURE_NEXT_STEPS.md` cross-reference each other, so links must be updated together.

## 3) Tracked sample reports in runtime output path (medium-high confidence)

Currently tracked under runtime output directories:

- `output/<station>/LocationData_{QualityReport,AggregationReport}.{json,md}`
- `output/NOAA Demo Data/{data_dictionary.html,pipeline_overview.html}`

Suggested move targets:

- `docs/examples/station_reports/...` for documentation artifacts
- or `tests/fixtures/reports/...` for test fixtures

Why:

- `output/` is also used for local generated runtime files
- Mixing tracked fixtures and local runtime outputs makes git status noisy

## 4) Legacy R material folder placement (medium confidence)

Current:

- `old_r_files/` containing old `.R` scripts plus old CSV snapshots

Suggested:

- `docs/legacy_r/` if retained for historical context
- otherwise delete data snapshots and keep only scripts in `docs/legacy_r/`

Why:

- Makes it explicit this is historical, not active pipeline code

## 5) Dated index snapshot placement (medium confidence)

Current tracked file:

- `noaa_file_index/20260207/README.md`

Suggested:

- `docs/data_snapshots/noaa_file_index_20260207.md` (if snapshot docs are retained)

Why:

- Avoids committing one-off dated runtime directories long-term

## Cleanup Risks / Linkage Checks

## 1) Existing modified tracked files

Tracked output report files under `output/` are currently modified in your workspace.  
Cleanup/moves should avoid accidental overwrite or revert.

## 2) Tests expecting local generated file

`tests/test_reproducibility_example.py` expects:

- `reproducibility/sample_station_cleaned_expected.csv`

But it is currently ignored/untracked. This is a reproducibility-risk mismatch.

Recommendation:

- Promote expected fixture to tracked status under `tests/fixtures/` or stop depending on an ignored local file.

## 3) Documentation drift found

README references missing files:

- `QC_SIGNALS_ARCHITECTURE.md`
- `CLEANING_RECOMMENDATIONS.md`

Recommendation:

- Either add these files or remove/update references.

## Suggested Cleanup Order (when you choose to execute)

1. Delete pure cache/log artifacts (`.coverage`, `.pytest_cache`, `__pycache__`, timing logs).
2. Move root scripts to `tools/` and fix references/import paths.
3. Move roadmap docs to `docs/roadmap/` and fix intra-doc links.
4. Decide policy for tracked `output/` report artifacts (fixtures vs docs examples) and relocate.
5. Prune/archive large ignored runtime outputs under `output/` and `noaa_file_index/`.
6. Resolve reproducibility fixture tracking (`sample_station_cleaned_expected.csv`).
7. Fix stale README references to missing docs.

## Decision Table

| Candidate | Action Type | Confidence | Notes |
|---|---|---|---|
| `.coverage`, `.pytest_cache`, `__pycache__` | Delete | High | Standard generated artifacts |
| `reprocess_timing*.log` | Delete | High | Local run logs |
| `output/*` generated CSVs | Delete/Archive | High | Regenerable, largest space |
| `noaa_file_index/20260207/*.csv` | Delete/Archive | High | Snapshot data, regenerable |
| `spec_coverage.csv` and related analysis CSVs | Delete/Regenerate | Medium | Referenced by tools/tests/docs |
| `check_station_sync.py` | Move | High | Operational utility |
| `rerun_stations.py` | Move | High | Operational utility |
| `generate_audit_queue.py` | Move | High | Docs already point to tools path |
| `NEXT_STEPS.md`, `ARCHITECTURE_NEXT_STEPS.md`, `P3_EXPAND_RESEARCH_VALUE.md` | Move | High | Better in docs roadmap area |
| Tracked report files in `output/<station>/` | Move | Medium-High | Better as fixtures/examples |
| `old_r_files/` | Move/Delete partial | Medium | Legacy/historical content |

