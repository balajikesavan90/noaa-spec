# Architecture Next Steps

Last reassessed: 2026-03-07

## 1. Current State

The parser/cleaner foundation is strong:

- `NEXT_STEPS.md` is now the completion record for spec-rule alignment and strict parsing behavior.
- `SPEC_COVERAGE_REPORT.md` reports full implemented and strict-tested coverage for extracted ISD rule families.
- Parsing breadth is no longer the primary bottleneck.

The next bottleneck is artifact credibility and researcher usability. This repository should now be treated as a scientific data publication system built on a specification-constrained parser and cleaner.

## 2. Updated Product Direction

This repository is not primarily an opinionated analysis pipeline. It is a publication system that produces reproducible scientific data artifacts:

- canonical cleaned datasets,
- domain-specific datasets,
- published quality/usability evidence,
- release manifests with lineage and reproducibility metadata.

The parser/cleaner remains the foundation, but the architecture focus is publication-grade contracts and artifact transparency.

## 3. Guiding Principles

- No big-bang rewrite: evolve incrementally inside `src/noaa_climate_data/`.
- Preserve and protect the existing spec-driven parser/cleaner/coverage foundation.
- Model architecture around published artifacts and their lineage graph.
- Contracts first: schemas, naming, null semantics, and provenance must be explicit and versioned.
- Deterministic and auditable outputs: identical inputs and config should produce identical artifact signatures.
- Prioritize researcher composability and joinability over built-in rollups.
- Keep changes PR-sized, compatibility-aware, and grounded in current package boundaries.

## 4. Artifact Model and Dataset Graph

Artifact flow:

```text
NOAA raw files
  -> specification-constrained parser/cleaner
  -> canonical cleaned dataset
  -> domain-specific datasets
  -> quality/usability reports
  -> release manifests
```

Artifact types:

- `canonical_dataset`: cleaned observation-level dataset that preserves NOAA semantics with standardized null/provenance behavior.
- `domain_dataset`: stable researcher-facing dataset for a specific domain projection of canonical data.
- `quality_report`: machine-readable and human-readable quality/usability evidence derived from canonical/domain artifacts.
- `release_manifest`: deterministic metadata record describing artifacts, schema versions, checksums, counts, and lineage for a build.

Required metadata for every artifact type:

- `artifact_id`
- `schema_version`
- `build_id`
- `input_lineage`
- `row_count`
- `checksum`
- `creation_timestamp`

`input_lineage` must resolve parent artifacts and/or source files so the full source-to-output chain is auditable.

## 5. Domain Dataset Registry

Target structure: module-based registry under `src/noaa_climate_data/domains/`.

Each domain module defines:

- `DOMAIN_NAME`
- `INPUT_FIELDS`
- `OUTPUT_SCHEMA`
- `JOIN_KEYS`
- `QUALITY_RULES`

Initial domain set:

- `core_meteorology`
- `wind`
- `precipitation`
- `clouds_visibility`
- `pressure_temperature`
- `remarks`

Domain dataset requirements:

- stable over release versions with explicit contract versioning,
- researcher-friendly and documented for direct use,
- joinable via shared identity keys,
- not aggregated products.

## 6. Published Quality Evidence

Quality evidence artifacts must be generated and published as first-class outputs alongside datasets:

- `field_completeness`
- `sentinel_frequency`
- `quality_code_exclusions`
- `domain_usability_summary`
- `station_year_quality`

These artifacts must be reproducible for a given build and linked in manifests via artifact IDs and lineage references.

## 7. Release Artifact Layout

Release outputs should follow a deterministic layout:

```text
release/
  build_<build_id>/
    canonical_cleaned/
    domains/
    quality_reports/
    manifests/
```

Layout, file naming, serialization settings, and manifest generation must be deterministic so reruns produce matching checksums when source inputs and configuration are unchanged.

## 8. Priority Roadmap

### Priority 0 - Publishability Release Gates (Must Complete First)

These gates block publishability. Complete these before Priority 1-5.

- [x] Repair documentation integrity so all referenced docs/scripts/tests exist and all KPI claims reflect current generated artifacts.
  - [x] Restore README compatibility links by adding `QC_SIGNALS_ARCHITECTURE.md` and `CLEANING_RECOMMENDATIONS.md` entrypoints.
  - [x] Regenerate suspicious-coverage summary and align README suspicious KPI claims with `spec_coverage.csv`.
  - [x] Rewrite `docs/PIPELINE_VALIDATION_PLAN.md` so referenced scripts/tests/commands match current repository interfaces.
  - [x] Refresh `noaa_file_index/20260207/README.md` runtime status sections to remove placeholder cleaning/aggregation guidance.
  - [x] Reconcile remaining README quantitative claims (test counts and milestone metrics) against current generated artifacts.
- [x] Promote `release/build_<build_id>/...` to the canonical publication surface and enforce it as the release contract path.
  - [x] Switch default `cleaning-run` roots to `release/build_<build_id>/{canonical_cleaned,quality_reports,manifests}`.
  - [x] Route default domain split outputs to `release/build_<build_id>/domains/<station_id>/`.
  - [x] Enforce release-path contract across remaining docs/runtime interfaces and remove legacy assumptions.
    - [x] Remove legacy `reprocess-output-dir` default domain-output root (`output/NOAA Demo Data`) and derive defaults from `--output-root` (`canonical_cleaned` sibling or `<output-root>/domains`).
    - [x] Update cleaning-run mode docs to state `release/build_<run_id>/{canonical_cleaned,domains,quality_reports,manifests}` as the default publication layout.
    - [x] Audit remaining CLI/docs references for non-release publication path assumptions.
- [x] Separate runtime outputs from publication artifacts, fixtures, and examples.
  - [x] Decouple integration test discovery from ambient `output/` state via explicit fixture-root configuration (`NOAA_INTEGRATION_OUTPUT_DIR`).
  - [x] Move tracked sample reports/demo outputs from `output/` into `docs/examples/` to avoid mixed runtime/tracked semantics.
  - [x] Publish explicit runtime vs publication boundary policy in `docs/ARTIFACT_BOUNDARY_POLICY.md`.
- [x] Remove or relocate operational run snapshots from publication-facing tracked locations.
  - [x] Remove tracked operational snapshots under `artifacts/test_runs/**` from version control.
  - [x] Add tracked-surface regression test to assert `artifacts/test_runs/**` and root `reprocess_timing*.log` are not tracked.
- [x] Eliminate domain-contract drift by centralizing domain-rule definitions and removing duplicated logic paths.
  - [x] Delegate `scripts/split_cleaned_by_domain.py` column classification to `noaa_climate_data.domain_split` (`COMMON_COLUMNS` + `classify_columns`).
  - [x] Hard-deprecate `scripts/split_domains_by_station.py` to remove parallel contract maintenance outside package-governed modules.
  - [x] Add regression test to enforce absence of duplicate script-level domain rule registries.
- [ ] Establish explicit artifact tracking policy (including `.gitignore` alignment) for release-grade CSV/Parquet datasets and manifests.

### Priority 1 - Dataset Contracts and Schema Discipline

- Freeze explicit contracts for `canonical_dataset`, each `domain_dataset`, each `quality_report` type, and `release_manifest`.
- Define and version canonical and domain schemas with stable column names, explicit null semantics, and provenance columns.
- Standardize shared identity keys and join keys across all dataset artifacts.
- Enforce no-sentinel leakage into cleaned numeric outputs before canonical publication.
- Encode required artifact metadata fields as contract-level requirements, not optional annotations.

### Priority 2 - Domain-Oriented Dataset Publishing

- [ ] Implement `src/noaa_climate_data/domains/` registry modules for the six initial domains.
  - [x] Add package registry skeleton and module set for `core_meteorology`, `wind`, `precipitation`, `clouds_visibility`, `pressure_temperature`, and `remarks`.
  - [ ] Wire registry definitions into domain publishing paths as the runtime source of truth.
- [ ] Require each domain module to declare `DOMAIN_NAME`, `INPUT_FIELDS`, `OUTPUT_SCHEMA`, `JOIN_KEYS`, and `QUALITY_RULES`.
  - [x] Add required declaration constants to each initial domain module and validate registry loading in tests.
  - [ ] Enforce declaration compatibility against emitted domain artifacts during release generation.
- [ ] Publish stable domain definitions and join documentation so cross-domain analyses do not depend on private pipeline details.
- [ ] Keep domains focused on reusable scientific data slices rather than derived aggregate products.

### Priority 3 - Data Quality and Usability Reporting

- Make `field_completeness`, `sentinel_frequency`, `quality_code_exclusions`, `domain_usability_summary`, and `station_year_quality` mandatory published artifacts.
- Add per-domain and per-field validity/usability indicators with clear exclusion semantics.
- Preserve QC attrition visibility so researchers can trace data loss from raw to published datasets.
- Publish quality artifacts in machine-readable formats and release-facing summaries.

### Priority 4 - Reproducibility, Manifests, and Lineage

- [ ] Implement deterministic writes for canonical, domain, and quality artifacts.
- [ ] Generate release manifests with schema versions, row counts, checksums, and artifact lineage links.
  - [x] Encode required metadata fields (`artifact_id`, `schema_version`, `build_id`, `input_lineage`, `row_count`, `checksum`, `creation_timestamp`) in station `_SUCCESS.json` artifact bundles.
  - [ ] Add release-manifest artifact rows for canonical/domain/quality outputs with contract metadata.
  - [ ] Validate manifest lineage links across canonical -> domains -> quality artifacts.
- [ ] Adopt the deterministic `release/build_<build_id>/...` layout as publication contract.
  - [x] Default `cleaning-run` path generation now targets `release/build_<build_id>/`.
  - [ ] Enforce canonical/domain/quality/manifest sibling layout for all write paths and modes.
- [ ] Capture reproducible build metadata (code revision, config identity, build timestamp, source scope).
- [ ] Ensure lineage links connect NOAA raw sources through canonical and domain outputs to released quality evidence.

### Priority 5 - CI and Validation Hardening

- Add CI schema validation for all artifact types (`canonical_dataset`, `domain_dataset`, `quality_report`, `release_manifest`).
- Add stale artifact detection between domain registry definitions, schemas, and generated outputs.
- Add reproducibility smoke tests that validate deterministic signatures for a bounded fixture build.
- Add smoke tests for end-to-end artifact graph generation (canonical -> domains -> quality -> manifests).
- Continue strict protection of parser/spec coverage guarantees established in `NEXT_STEPS.md`.

## 9. Deferred / Out of Scope

The following are deferred and out of scope for the near-term architecture roadmap:

- built-in aggregate outputs as a core product artifact,
- opinionated rollup logic embedded in publication flows,
- downstream analytical summarization.

These are downstream researcher responsibilities using published canonical/domain datasets and quality evidence.

## 10. Implementation Strategy

Delivery remains incremental and PR-based inside the existing package, not an architectural overhaul.

Recommended execution waves:

1. Establish artifact contracts and required metadata fields for canonical/domain/quality/manifest outputs.
2. Add deterministic release layout and manifest generation with checksums and lineage.
3. Implement domain registry modules under `src/noaa_climate_data/domains/` and wire stable domain publishing.
4. Promote quality evidence generation to required release artifacts and bind them into manifests.
5. Harden CI with schema, lineage, stale-artifact, and reproducibility validation gates.

Compatibility expectations:

- Keep current parser/cleaner behavior as the preserved foundation.
- Introduce artifact-oriented contracts without break-first migration.
- Use explicit deprecation windows for any legacy naming/path transitions.

## 11. Appendix - Current Publishability Gap Inventory (Supports Priority 0)

These are repository-specific publishability blockers discovered during full-repo review. This appendix provides concrete evidence for Priority 0 release gates.

### 11.1 Documentation Integrity Gaps

- `README.md` links to missing files:
  - `QC_SIGNALS_ARCHITECTURE.md`
  - `CLEANING_RECOMMENDATIONS.md`
- `docs/PIPELINE_VALIDATION_PLAN.md` references many scripts/tests/artifacts that do not exist in the repository (for example `tools/spec_coverage/sample_audit_rules.py`, `tools/spec_coverage/export_suspicious_cases.py`, and multiple `tests/test_*` files).
- `docs/PIPELINE_VALIDATION_PLAN.md` includes command/interface drift against existing scripts (for example `tools/spec_coverage/generate_audit_queue.py --sample-size 50`, while current script interface is `--k`, `--limit`, `--format`, and `--out`).
- KPI text in `docs/PIPELINE_VALIDATION_PLAN.md` is stale versus current generated state in `SPEC_COVERAGE_REPORT.md`.
- `docs/validation_artifacts/suspicious_coverage/suspicious_summary.md` is stale relative to current `spec_coverage.csv` and `tests/test_suspicious_coverage_integrity.py` behavior.
- `README.md` suspicious-coverage KPI text is stale versus current generated artifacts (`SPEC_COVERAGE_REPORT.md` and `spec_coverage.csv`).
- `noaa_file_index/20260207/README.md` still documents cleaning/aggregation as placeholders, but those entrypoints now exist.

### 11.2 Publication Boundary and Artifact Path Gaps

- Runtime defaults in `src/noaa_climate_data/cleaning_runner.py` currently target `artifacts/test_runs/<run_id>/...` and `artifacts/parquet_runs/<run_id>/...`, not the publication contract path `release/build_<build_id>/...`.
- Root-level generated governance artifacts (`spec_coverage.csv`, `rule_impact_summary.csv`, `RULE_PROVENANCE_LEDGER.csv`, etc.) are not yet organized as versioned release-scoped artifacts.
- Tracked run-instance snapshots exist under `artifacts/test_runs/.../manifests/run_config.json`; these are operational run records, not release artifacts.
- Tracked run-instance snapshots include machine-specific absolute paths in `run_config.json`, which is operational metadata leakage and not publication-grade lineage metadata.
- `output/` is currently mixed-use (runtime data + committed sample reports), which weakens publication boundary clarity.
- Deprecated `reprocess-output-dir` behavior in `src/noaa_climate_data/cli.py` still defaults domain split writes to `output/NOAA Demo Data`, reinforcing mixed runtime/publication boundaries.
- `tests/test_integration.py` depends on `output/` location semantics, coupling tests to runtime paths rather than explicit fixtures/contracts.
- Dated index snapshot content (`noaa_file_index/20260207/*.csv`) is tracked directly in runtime path structure rather than in an explicit release/snapshot contract area.
- Transient operational timing logs (`reprocess_timing*.log`) are tracked at repo root, creating publication-surface noise.

### 11.3 Contract Drift and Maintenance Risk

- Domain classification logic is duplicated between:
  - `src/noaa_climate_data/domain_split.py`
  - `scripts/split_cleaned_by_domain.py`
  This creates drift risk for domain dataset contracts.
- A second legacy/parallel split path exists in `scripts/split_domains_by_station.py`, creating additional domain contract drift surface outside package-governed modules.
- Operational helper scripts live at repo root (`check_station_sync.py`, `rerun_stations.py`, `generate_audit_queue.py`) rather than scoped `tools/` modules, which weakens boundary discipline.
- Required release metadata contract (`artifact_id`, `schema_version`, `build_id`, `input_lineage`, `row_count`, `checksum`, `creation_timestamp`) is not yet encoded in existing run manifests (`run_manifest.csv`, `run_status.csv`, `_SUCCESS.json`) produced by `cleaning_runner.py`.
- No explicit, versioned schema-contract files are currently published for canonical/domain/quality/manifest artifacts, which blocks contract freeze enforcement and CI schema validation gates.
- Legacy R historical assets (`old_r_files/` scripts + CSV snapshots) are colocated in active repository surface without an explicit archive/legacy boundary, increasing maintenance and publication-scope ambiguity.

### 11.4 Version-Control Policy Gap for Publishable Artifacts

- `.gitignore` currently ignores `*.csv` and `*.parquet` globally. This is convenient for local iteration but conflicts with publishing deterministic dataset artifacts unless release outputs are explicitly whitelisted and policy-documented.

### 11.5 Priority 0 Closure Checklist

1. Repair all broken/stale docs so repository docs are executable and current.
2. Make `release/build_<build_id>/...` the canonical publication surface and document it as the only release contract path.
3. Separate runtime outputs from publication fixtures/examples/tests.
4. Remove or relocate operational run snapshots from tracked publication-facing locations.
5. Eliminate duplicated domain-rule logic and centralize domain contract definitions.
6. Tighten artifact tracking policy (`.gitignore` + explicit inclusion rules) for release-grade datasets and manifests.

### 11.6 Priority 0 Execution Table (Owner + Artifact + Acceptance)

| Gate | Primary Owner Role | Primary Deliverable Artifact(s) | Acceptance Check (Publishability Gate) |
| --- | --- | --- | --- |
| Documentation integrity repair | Documentation maintainer + module owners | Updated `README.md`, `docs/PIPELINE_VALIDATION_PLAN.md`, regenerated `docs/validation_artifacts/suspicious_coverage/suspicious_summary.md` | Every referenced script/test/doc exists; all commands execute with current interfaces; KPI numbers in docs match regenerated artifacts in the same commit. |
| Canonical release publication surface | Pipeline architect + release engineering | `release/build_<build_id>/` writer pathing and updated run docs | Release build writes only to `release/build_<build_id>/{canonical_cleaned,domains,quality_reports,manifests}`; no release contract paths point to `output/` or ad hoc roots. |
| Runtime vs publication boundary separation | Data engineering + test engineering | Fixture policy doc + relocated fixtures/examples + runtime path cleanup | Tests use explicit fixtures/contracts (not ambient `output/` state); runtime outputs are excluded from publication-facing tracked areas. |
| Operational snapshot relocation | Repo maintainer | Removal/relocation of tracked operational run snapshots and timing logs | No tracked run-instance machine snapshots remain under publication-facing locations; no root-level transient timing logs remain tracked. |
| Domain contract centralization | Domain data owner | Single package-governed domain contract module set (registry + classifiers) | Domain split/classification rules are defined in one source of truth under `src/noaa_climate_data/`; legacy duplicate logic paths are removed or hard-deprecated. |
| Artifact tracking and inclusion policy | Repo maintainer + release engineering | Updated `.gitignore` + explicit release include policy doc | Policy allows deterministic release CSV/Parquet/manifests to be versioned where required; non-release operational outputs remain excluded by default. |
| Manifest metadata contract enforcement | Release engineering + pipeline architect | Manifest schema + manifest writer updates + validation tests | Produced manifests include `artifact_id`, `schema_version`, `build_id`, `input_lineage`, `row_count`, `checksum`, `creation_timestamp` for every published artifact. |
| Versioned schema contract publication | Data contract owner | Versioned schema contract files for canonical/domain/quality/manifest artifacts | Canonical/domain/quality/manifest schema contracts exist, are versioned, and are validated in CI against produced artifacts. |
| Legacy surface isolation | Repo maintainer | Legacy archive boundary (`docs/legacy_r/` or equivalent) + references update | Legacy R assets are moved to an explicit legacy/archive boundary or removed; active docs/code no longer imply legacy directories are part of release surface. |
