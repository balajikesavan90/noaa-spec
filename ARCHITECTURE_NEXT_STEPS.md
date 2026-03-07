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

### Priority 1 - Dataset Contracts and Schema Discipline

- Freeze explicit contracts for `canonical_dataset`, each `domain_dataset`, each `quality_report` type, and `release_manifest`.
- Define and version canonical and domain schemas with stable column names, explicit null semantics, and provenance columns.
- Standardize shared identity keys and join keys across all dataset artifacts.
- Enforce no-sentinel leakage into cleaned numeric outputs before canonical publication.
- Encode required artifact metadata fields as contract-level requirements, not optional annotations.

### Priority 2 - Domain-Oriented Dataset Publishing

- Implement `src/noaa_climate_data/domains/` registry modules for the six initial domains.
- Require each domain module to declare `DOMAIN_NAME`, `INPUT_FIELDS`, `OUTPUT_SCHEMA`, `JOIN_KEYS`, and `QUALITY_RULES`.
- Publish stable domain definitions and join documentation so cross-domain analyses do not depend on private pipeline details.
- Keep domains focused on reusable scientific data slices rather than derived aggregate products.

### Priority 3 - Data Quality and Usability Reporting

- Make `field_completeness`, `sentinel_frequency`, `quality_code_exclusions`, `domain_usability_summary`, and `station_year_quality` mandatory published artifacts.
- Add per-domain and per-field validity/usability indicators with clear exclusion semantics.
- Preserve QC attrition visibility so researchers can trace data loss from raw to published datasets.
- Publish quality artifacts in machine-readable formats and release-facing summaries.

### Priority 4 - Reproducibility, Manifests, and Lineage

- Implement deterministic writes for canonical, domain, and quality artifacts.
- Generate release manifests with schema versions, row counts, checksums, and artifact lineage links.
- Adopt the deterministic `release/build_<build_id>/...` layout as publication contract.
- Capture reproducible build metadata (code revision, config identity, build timestamp, source scope).
- Ensure lineage links connect NOAA raw sources through canonical and domain outputs to released quality evidence.

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
