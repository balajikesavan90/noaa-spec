# Architecture next steps: normalized checklist

Last reassessed: 2026-03-07

This file is the implementation checklist and source of truth for architecture and
productization work.

`NEXT_STEPS.md` is now a completed parser/spec alignment record (all checklist items
checked as of this reassessment). This file now carries the remaining structural,
contract, release, and publication backlog.

## Status key

- [x] Completed in the repository
- [ ] Open
- [ ] Open (partial: some implementation exists, but contract-level completion is missing)

## Priority recommendation: `NEXT_STEPS.md` vs architecture work

- [x] Keep `NEXT_STEPS.md` as correctness evidence for parser/cleaning semantics.
- [x] Treat spec-rule implementation work as complete baseline.
- [ ] Shift active effort toward architecture/productization (~80%) and targeted regression hardening (~20%).
- [ ] Keep architecture work incremental inside `src/noaa_climate_data/` (no big-bang rewrite).

## P0: conflict normalization (lock these decisions first)

- [ ] Adopt `schemas/` as the canonical contract location; treat `data_contracts/` as deprecated naming.
- [ ] Standardize raw partitioning to `layer=raw_station/station_bucket=<00-ff>/year=<yyyy>/month=<mm>/` and keep `station_id` in file name/metadata (not a partition directory).
- [ ] Standardize clean partitioning to `layer=clean_station/station_bucket=<00-ff>/year=<yyyy>/month=<mm>/`.
- [ ] Standardize curated partitioning to `layer=curated/dataset=<metric>_station/station_bucket=<00-ff>/year=<yyyy>/month=<mm>/`.
- [ ] Standardize aggregated partitioning to `layer=aggregated/dataset=<metric>_<grain>/year=<yyyy>/month=<mm>/` (omit `month` for yearly or normals outputs).
- [ ] Keep canonical natural keys (`station_id`, `timestamp_utc`, `year`, `month`, `day`, `hour`) and add deterministic `record_id` hash for observation-level joins/dedup. (partial: time dimensions exist, canonical contract and `record_id` do not)
- [ ] Standardize provenance column naming with `meta_` prefix: `meta_run_id`, `meta_dataset_version`, `meta_pipeline_commit`, `meta_processed_at_utc`, `meta_source_year`, `meta_source_file_name`, `meta_parent_snapshot_id`.
- [ ] Keep raw NOAA quality/code fields and add derived usability fields (`*_qc_status`, `*_qc_pass`, `*_usable`) in clean/curated outputs. (partial: `*_qc_status`/`*_qc_pass` plus row-level usability summaries exist)
- [ ] Canonicalize CLI names to `build-clean-station`, `build-curated`, `build-aggregates`, `validate`, `publish-release`, `run --config`; keep compatibility aliases for `build-metric-stations` and `build-release`.
- [ ] Canonicalize release artifacts to `checksums.sha256` and `CHANGELOG_DATASET.md` (keep root `CHANGELOG.md` for code changes).
- [ ] Use both contract layers: versioned JSON schemas for persisted datasets plus Pandera checks in pipeline/runtime validation.

## P1: repository architecture and compatibility boundaries

- [x] Keep incremental migration in `src/noaa_climate_data/` (no big-bang rewrite).
- [ ] Extract modules with clear boundaries: `ingestion`, `parsing`, `cleaning`, `transforms`, `aggregation`, `validation`, `metadata`, `publish`, `io`, `orchestration`, `observability`. (partial: `pdf_markdown`, `domain_split`, and `research_reports` added, but core boundaries still concentrated in `pipeline.py`)
- [ ] Keep `constants.py`, `cleaning.py`, and `pipeline.py` as compatibility facades while internal modules are extracted. (partial: modules are still mostly implementation centers, not facades)
- [ ] Add `src/noaa_climate_data/api.py` as the stable Python API surface.
- [ ] Add `src/noaa_climate_data/config.py` and central config loading for paths, partitions, manifests, and release settings.
- [ ] Move root one-off scripts into `scripts/` or CLI commands.
- [ ] Define internal/private helpers with `_` prefix and keep them out of public docs. (partial: helper naming is mostly present, but policy and docs boundary are not formalized)

## P2: dataset layering and schema contracts

- [ ] Implement and freeze layer contracts for `raw_station`, `clean_station`, curated metric station datasets, aggregated datasets, and published release datasets.
- [ ] Add versioned JSON schemas in `schemas/` for each dataset and grain.
- [ ] Define required metadata columns and nullable policy in schema files (no sentinel leakage in numeric outputs).
- [ ] Define station identity contract (`station_id`, `station_usaf`, `station_wban`) and source identity contract (`meta_source_file_name`, `meta_source_year`).
- [ ] Add uniqueness constraints for natural key and `record_id` at observation grains.
- [ ] Add schema migration notes for every backward-incompatible contract change.

## P3: manifests, lineage, and storage reliability

- [ ] Add `manifests/ingestion/<run_id>.parquet` (one row per station-year pull attempt).
- [ ] Add `manifests/dataset/<layer>/<snapshot_id>.json` with schema version, partition spec, row/file counts, null rates, and checksums.
- [ ] Add lineage tracking fields and manifest graph (raw -> clean -> curated -> aggregated -> published).
- [ ] Add deterministic parquet write settings and sort behavior for reproducible outputs.
- [ ] Add atomic write flow (temp write -> checksum verify -> commit marker).
- [ ] Add compaction plan for clean/curated/aggregated layers to control tiny files.
- [ ] Replace mutable-only station status booleans with manifest-derived run status views (keep booleans temporarily for compatibility). (partial: booleans exist and are actively used)
- [ ] Add upload retry/resume and partial-failure handling for object-store publishing.

## P4: CLI/API contract hardening and run orchestration

- [x] Keep existing commands stable (`file-list`, `location-ids`, `pick-location`, `clean-parquet`, `process-location`) until deprecation windows are published.
- [ ] Add/finish commands: `ingest-raw`, `build-clean-station`, `build-curated`, `build-aggregates`, `validate`, `publish-release`, `run --config`.
- [ ] Add explicit deprecation policy for command and argument changes in README.
- [ ] Document idempotency and overwrite behavior per command.
- [ ] Implement run IDs and structured logging context in all pipeline entry points.
- [ ] Add minimal stable API functions: `build_file_index`, `build_station_registry`, `build_clean_station`, `build_curated_station`, `build_aggregates`, `publish_release`, `run_pipeline`.

## P5: quality usability and user-facing utility datasets

- [x] Add row-level usability signals (`row_has_any_usable_metric`, `usable_metric_count`, `usable_metric_fraction`).
- [ ] Add station-level usability outputs (coverage percentages, quality score/tier).
- [ ] Ensure aggregates include completeness metadata (`obs_count`, `usable_obs_count`, `coverage_pct`).
- [ ] Add curated-derived metrics (dual units, humidity/comfort metrics, wind utility metrics, precipitation intensity where valid). (partial: dual-unit conversion support exists)
- [ ] Add completeness outputs: `station_completeness_daily`, `station_completeness_monthly`, `station_quality_monthly`.
- [ ] Add metadata tables: `dim_station`, `dim_variable`, `fact_station_coverage_daily`, `fact_station_quality_monthly`, `fact_processing_runs`, `dim_dataset_release`.
- [ ] Add machine-readable dataset catalog and sample query/notebook assets. (partial: human-readable reports and data dictionary outputs exist)

## P6: validation, testing, and CI governance

- [ ] Add Pandera-based runtime validation profiles for clean/curated/aggregated writes.
- [ ] Add schema contract tests against versioned JSON schemas.
- [ ] Add dataset-level contract tests under `tests/contract/` or `tests/contracts/` (pick one path and standardize).
- [ ] Add regression links to architecture open items (replace obsolete linkage to `NEXT_STEPS.md`).
- [ ] Add property-based tests (Hypothesis) for malformed/edge NOAA encodings.
- [ ] Add deterministic smoke-test fixture and expected outputs for CI. (partial: smoke-style tests exist, but no contract fixture set)
- [ ] Add GitHub Actions for lint, type-check, tests, schema contracts, manifest validation, and smoke pipeline run. (partial: suspicious-coverage workflow exists)
- [ ] Require validation-report generation on release branches before tagging.

## P7: publication and DOI release workflow

- [ ] Implement `publish-release` workflow that builds immutable `published/release=vX.Y.Z/` artifacts.
- [ ] Include required release artifacts: parquet snapshots, dataset manifests, `checksums.sha256`, schema bundle, `DATA_DICTIONARY.md`, `README_RELEASE.md`, `CHANGELOG_DATASET.md`, `CITATION.cff`, `LICENSE`, `PROVENANCE.md`.
- [ ] Add semantic version policy for dataset releases (major/minor/patch compatibility rules).
- [ ] Add automated release packaging for GitHub Release outputs.
- [ ] Add Zenodo deposition metadata template and DOI linkage process.
- [ ] Add release validation checks that block publish when manifests/checksums/citation artifacts are missing.

## P8: methods paper readiness and evidence artifacts

- [ ] Finalize methods outline tied to implemented pipeline stages.
- [ ] Run validation experiments: parse fidelity, coverage deltas, QC attrition, cross-source comparisons, reproducibility reruns. (partial: quality/aggregation report generation exists)
- [ ] Run scaling benchmarks by station count and year window. (partial: timing logs exist, benchmark contract does not)
- [ ] Produce paper figures (architecture DAG, coverage, QC waterfall, scaling).
- [ ] Produce paper tables (schema summary, QC policy matrix, validation thresholds, release diffs).
- [ ] Add reproducibility appendix with exact config, versions, manifests, and checksums. (partial: reproducibility scaffolding exists without architecture manifests/checksums)

## P9: PR-sized execution order (re-baselined)

- [ ] PR 1: Add `config.py`, `configs/runs/`, and `run --config` as the canonical execution path.
- [ ] PR 2: Introduce stable API surface (`api.py`) and map existing pipeline entry points to it.
- [ ] PR 3: Finalize dataset/layer contracts and partition specs; document key/provenance columns.
- [ ] PR 4: Add deterministic parquet writer helpers, atomic commit markers, and normalized partition utilities.
- [ ] PR 5: Add `schemas/` (versioned JSON schemas) and clean-layer schema enforcement.
- [ ] PR 6: Add ingestion and dataset manifests plus manifest-derived run status views.
- [ ] PR 7: Replace `aggregate-parquet` placeholder with production `build-aggregates` behavior and completeness metadata.
- [ ] PR 8: Implement curated build flows and curated metric datasets (keep compatibility aliases where needed).
- [ ] PR 9: Add `validate` command, schema contract tests, and property-based malformed-input tests.
- [ ] PR 10: Expand CI from suspicious coverage checks to lint/type/test/smoke/schema/manifest gates.
- [ ] PR 11: Implement `publish-release` packaging, checksums/changelog/citation artifacts, and release validation gates.
- [ ] PR 12: Run bounded release-candidate dry run, publish validation report, and capture methods-paper evidence outputs.
